from constructs import Construct

import aws_cdk as core

from aws_cdk import (
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    aws_kms as kms,
    aws_s3 as s3
)




class CdkStack(Stack):

    def __init__(self, scope: Construct, stack_name: str, account: str, region: str, tags, params, **kwargs) -> None:
        environment = core.Environment(account=account, region=region)

        super().__init__(scope, stack_name=stack_name, env=environment, tags=tags,  **kwargs)
        
        vpc_tags = {
        'name' : 'MWAAEnvironment' 
        }
        
        # Create VPC network for mwaa

        self.vpc = ec2.Vpc(
            self,
            id="MWAA-Hybrid-ApacheAirflow-VPC",
            cidr="10.192.0.0/16",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public", cidr_mask=24,
                    reserved=False, subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(
                    name="private", cidr_mask=24,
                    reserved=False, subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )

        bucket = s3.Bucket(self, "S3bucktMWAATest",
            bucket_name="buck5tr",
            versioned=True,
            auto_delete_objects=False,
            block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
# bucket_key_enabled= True,
            encryption= s3.BucketEncryption.S3_MANAGED)
            
        dags_bucket_arn = bucket.bucket_arn

        core.Tags.of(bucket).add("Name", "mwaa_buck")
        core.Tags.of(bucket).add("env", "MWAAEnvironment")
        core.Tags.of(bucket).add("service", "MWAA_Apache_Airflow")
        core.Tags.of(bucket).add("service", "MWAA_Apache_Airflow")
        core.Tags.of(self.vpc).add("Name", "MWAAEnvironment")

#    Below code to deploy the dag folder and files in s3 bucket
        s3deploy.BucketDeployment(self, "DeployDAG",
        sources=[s3deploy.Source.asset("./dags")],
        destination_bucket=bucket,
        destination_key_prefix="dags",
        prune=False,
        retain_on_delete=False
        )

# Add policies
        mwaa_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=["airflow:PublishMetrics"],
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:airflow:{self.region}:{self.account}:environment/{params["env_name"]}"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:ListAllMyBuckets"
                    ],
                    effect=iam.Effect.DENY,
                    resources=[
                        f"{dags_bucket_arn}/*",
                        f"{dags_bucket_arn}"
                        ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "s3:*"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"{dags_bucket_arn}/*",
                        f"{dags_bucket_arn}"
                        ],
                ),
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogStream",
                        "logs:CreateLogGroup",
                        "logs:PutLogEvents",
                        "logs:GetLogEvents",
                        "logs:GetLogRecord",
                        "logs:GetLogGroupFields",
                        "logs:GetQueryResults",
                        "logs:DescribeLogGroups"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:logs:{self.region}:{self.account}:log-group:airflow-{params['env_name']}-*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "logs:DescribeLogGroups"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "sqs:ChangeMessageVisibility",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes",
                        "sqs:GetQueueUrl",
                        "sqs:ReceiveMessage",
                        "sqs:SendMessage"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[f"arn:aws:sqs:{self.region}:*:airflow-celery-*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "ecs:RunTask",
                        "ecs:DescribeTasks",
                        "ecs:RegisterTaskDefinition",
                        "ecs:DescribeTaskDefinition",
                        "ecs:ListTasks"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        "*"
                        ],
                    ),
                iam.PolicyStatement(
                    actions=[
                        "iam:PassRole"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=[ "*" ],
                    conditions= { "StringLike": { "iam:PassedToService": "ecs-tasks.amazonaws.com" } },
                    ),
                iam.PolicyStatement(
                    actions=[
                        "kms:Decrypt",
                        "kms:DescribeKey",
                        "kms:GenerateDataKey*",
                        "kms:Encrypt",
                        "kms:PutKeyPolicy"
                    ],
                    effect=iam.Effect.ALLOW,
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": [
                                f"sqs.{self.region}.amazonaws.com",
                                f"s3.{self.region}.amazonaws.com",
                            ]
                        }
                    },
                ),
            ]
        )

        mwaa_service_role = iam.Role(
            self,
            "mwaa-service-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("airflow.amazonaws.com"),
                iam.ServicePrincipal("airflow-env.amazonaws.com"),
                iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            ),
            inline_policies={"CDKmwaaPolicyDocument": mwaa_policy_document},
            path="/service-role/")

# Creation of security group for mwaa environment

        security_group = ec2.SecurityGroup(
            self,
            id = "mwaa-sg",
            vpc = vpc,
            security_group_name = "mwaa-sg"
        )

        security_group_id = security_group.security_group_id

        security_group.connections.allow_internally(ec2.Port.all_traffic(),"MWAA")

        subnets = [subnet.subnet_id for subnet in vpc.private_subnets]
        network_configuration = mwaa.CfnEnvironment.NetworkConfigurationProperty(
            security_group_ids=[security_group_id],
            subnet_ids=subnets)

#logging configurations

        logging_configuration = mwaa.CfnEnvironment.LoggingConfigurationProperty(
            dag_processing_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True,
                log_level="INFO"
            ),
            task_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True,
                log_level="INFO"
            ),
            worker_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True,
                log_level="INFO"
            ),
            scheduler_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True,
                log_level="INFO"
            ),
            webserver_logs=mwaa.CfnEnvironment.ModuleLoggingConfigurationProperty(
                enabled=True,
                log_level="INFO"
            ))

#Creation of managed airflow environment


    managed_airflow = mwaa.CfnEnvironment(
            scope=self,
            id='airflow-test-environment',
            name=f"{params['env_name']}",
            airflow_configuration_options={'core.default_timezone': 'utc'},
            airflow_version='2.0.2',
            dag_s3_path="dags",
            environment_class='mw1.small',
            execution_role_arn=mwaa_service_role.role_arn,
            #kms_key=key.key_arn,
            logging_configuration=logging_configuration,
            max_workers=5,
            network_configuration=network_configuration,
            #plugins_s3_object_version=None,
            #plugins_s3_path=None,
            #requirements_s3_object_version=None,
            #requirements_s3_path=None,
            source_bucket_arn=dags_bucket_arn,
            webserver_access_mode='PUBLIC_ONLY',
            #weekly_maintenance_window_start=None
        )

# Some parameters of mwaa and the tags
        options = {
            'core.load_default_connections': False,
            'core.load_examples': False,
            'webserver.dag_default_view': 'tree',
            'webserver.dag_orientation': 'TB'
        }

        tags = {
            'env': f"{params['env_name']}",
            'service': 'MWAA Apache AirFlow'
            'Name': f"{params['env_name']}"}

        managed_airflow.add_override('Properties.AirflowConfigurationOptions', options)
        managed_airflow.add_override('Properties.Tags', tags)



    # def define_rds(self,params):

            # vpc = ec2.Vpc.from_lookup(self, 'VPC' + '_' + params["name"], vpc_id=params["vpc_id"])

            # retention = Duration.days(7)
    # #        key = kms.Ikey("arn:aws:kms:us-east-1:409599951855:key/20c09f0c-e88a-4b33-aaef-d1e675c3f28e")


            # engine = rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_11_13)
            # rds.DatabaseInstance(self, "akamai_db",
                             # engine=engine,
                             # database_name = "akamai-db",
                             # instance_type = ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.LARGE),
                             # license_model = rds.LicenseModel.GENERAL_PUBLIC_LICENSE,
                             # availability_zone = "us-east-1c",
                             # backup_retention = retention,
                             # cloudwatch_logs_exports = ["upgrade"],
                             # copy_tags_to_snapshot = True,
                             # vpc=vpc,
                             # deletion_protection = True,
                             # enable_performance_insights = True,
                             # instance_identifier = "akamai_db",
                             # iops = 2000,
                             # max_allocated_storage = 1500,
 # #                           performance_insight_encryption_key = ["arn:aws:kms:us-east-1:409599951855:key/20c09f0c-e88a-4b33-aaef-d1e675c3f28e"],
                             # port = 5432,
                             # publicly_accessible = False,
 # #                            security_groups = ["sg-c98b59be", "sg-d71df7a0"],
                             # storage_type = rds.StorageType.IO1,
                             # credentials=rds.Credentials.from_generated_secret("postgres")
                             # )

            # rds.DatabaseInstance(self, "InstanceWithUsernameAndPassword",
            #                  engine=engine,
            #                  vpc=vpc,
            #                  credentials=rds.Credentials.from_password("postgres",
            #                                                            SecretValue.ssm_secure("/dbPassword", "1"))
            #                  )
            #
            # my_secret = secretsmanager.Secret.from_secret_name(self, "DBSecret", "myDBLoginInfo")
            # rds.DatabaseInstance(self, "InstanceWithSecretLogin",
            #                  engine=engine,
            #                  vpc=vpc,
            #                  credentials=rds.Credentials.from_secret(my_secret)
            #                  )
#send output to the cdk console as well as to the cloudformation

        CfnOutput(
            self,
            id="VPCId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name=f"{self.region}:{self.account}:{self.stack_name}:vpc-id"
        )
        
        CfnOutput(
            self,
            id="MWAASecurityGroup",
            value=security_group_id,
            description="Security Group name used by MWAA")