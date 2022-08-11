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

    def __init__(self, scope: Construct, stack_name: str, account: str, region: str, tags, **kwargs) -> None:
        environment = core.Environment(account=account, region=region)

        super().__init__(scope, stack_name=stack_name, env=environment, tags=tags,  **kwargs)

        bucket = s3.Bucket(self, "S3buckTest",
            bucket_name="hp-boe",
            versioned=False,
            auto_delete_objects=False,
            block_public_access = s3.BlockPublicAccess.BLOCK_ALL,
 #           bucket_key_enabled= True,
            encryption= s3.BucketEncryption.S3_MANAGED)

        core.Tags.of(bucket).add("Owner", "Enablement_for BOE_Dashboard")
        core.Tags.of(bucket).add("Category", "Enablement")
        core.Tags.of(bucket).add("Sub-Category", "Enablement")
        core.Tags.of(bucket).add("Name", "Enablement_S3")



    def define_rds(self,params):

            vpc = ec2.Vpc.from_lookup(self, 'VPC' + '_' + params["name"], vpc_id=params["vpc_id"])

            retention = Duration.days(7)
    #        key = kms.Ikey("arn:aws:kms:us-east-1:409599951855:key/20c09f0c-e88a-4b33-aaef-d1e675c3f28e")


            engine = rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_11_13)
            rds.DatabaseInstance(self, "akamai_db",
                             engine=engine,
                             database_name = "akamai-db",
                             instance_type = ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.LARGE),
                             license_model = rds.LicenseModel.GENERAL_PUBLIC_LICENSE,
                             availability_zone = "us-east-1c",
                             backup_retention = retention,
                             cloudwatch_logs_exports = ["upgrade"],
                             copy_tags_to_snapshot = True,
                             vpc=vpc,
                             deletion_protection = True,
                             enable_performance_insights = True,
                             instance_identifier = "akamai_db",
                             iops = 2000,
                             max_allocated_storage = 1500,
 #                           performance_insight_encryption_key = ["arn:aws:kms:us-east-1:409599951855:key/20c09f0c-e88a-4b33-aaef-d1e675c3f28e"],
                             port = 5432,
                             publicly_accessible = False,
 #                            security_groups = ["sg-c98b59be", "sg-d71df7a0"],
                             storage_type = rds.StorageType.IO1,
                             credentials=rds.Credentials.from_generated_secret("postgres")
                             )

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


