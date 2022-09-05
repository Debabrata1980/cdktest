import aws_cdk.aws_iam as iam
from collections import namedtuple

# Stack name must match the regular expression: /^[A-Za-z][A-Za-z0-9-]*$/
# Replace with a custom name for your stack
STACK_NAME = "tiger-analytics"

# Account ID
ACCOUNT = "273641968769"
# Region to be deployed
REGION = "us-west-2"
# Tags - replace values
TAGS = {"Category": "mPulse", "Subcategory": "Data_Foundation", "Name":"mPulse_RDS","Owner": "mPulse"}

# Disks - attachments
Disk = namedtuple("Disk", ["name", "size", "type"])
# Network Rules
Rule = namedtuple("Rule", ["destination", "port", "protocol"])

# Policies definition, add permissions to access other aws services
DOCUMENT_POLICY = [
    iam.PolicyStatement(sid="EnablePutLogs",
                        effect=iam.Effect.ALLOW,
                        actions=["logs:PutLogEvents"],
                        resources=["arn:aws:logs:*:409599951855:log-group:*:log-stream:*"]
                        ),
    iam.PolicyStatement(sid="EnableCreateLogs",
                        effect=iam.Effect.ALLOW,
                        actions=["logs:CreateLogStream", "logs:CreateLogGroup"],
                        resources=["arn:aws:logs:*:409599951855:log-group:*"]
                        ),
    iam.PolicyStatement(sid="S3Access",
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListBucket", "s3:GetObject"],
                        resources=["arn:aws:s3:::c360-external-share", "arn:aws:s3:::c360-external-share/*"])
]

ingress_rules = [
    Rule(destination="15.0.0.0/9", port=3389, protocol="tcp"),
    Rule(destination="172.29.23.147/32", port=3389, protocol="tcp"),
    Rule(destination="172.29.18.162/32", port=3389, protocol="tcp"),
    Rule(destination="172.20.134.153/32", port=3389, protocol="tcp"),
    Rule(destination="172.20.149.251/32", port=3389, protocol="tcp"),
    Rule(destination="172.29.22.202/32", port=3389, protocol="tcp"),
    Rule(destination="172.20.137.146/32", port=3389, protocol="tcp"),
    Rule(destination="172.20.132.202/32", port=3389, protocol="tcp")
]


disks = [
    # Disk(name="/dev/sdb", size=2000, type="GP2")
]

# Stack EC2 params
# Replace current for custom parameters
PARAMS = {
    "name": "Akamai_RDS",  # RDS instance name
    "instance_type": "db.m5.xlarge",  # one of https://aws.amazon.com/ec2/instance-types/
    "ami_id": "ami-079fddfb11f574925",  # Image Id to use in the EC2
    "key_name": "tiger_analytics",  # Registered key name for ssh access
    "vpc_id": "vpc-547b782c",
    "subnet_type": "PRIVATE",
    "network_rules_ingress": ingress_rules,
    "disks": disks,
    "policy": DOCUMENT_POLICY,
}

# Data Science ML EC2 for Tiger Analytics

ml_ingress_rules = [
    Rule(destination="15.0.0.0/9", port=3389, protocol="tcp"),
    Rule(destination="170.20.147.173/32", port=3389, protocol="tcp"),  # mohammed.naseef1@hp.com workspace IP
    Rule(destination="172.20.145.51/32", port=3389, protocol="tcp")  # venkatesh.arramshetti@hp.com workspace IP
]

ml_disks = [
    # Disk(name="/dev/sdb", size=2000, type="GP2")
]

# Policies definition, add permissions to access other aws services
ML_DOCUMENT_POLICY = [
    iam.PolicyStatement(sid="EnablePutLogs",
                        effect=iam.Effect.ALLOW,
                        actions=["logs:PutLogEvents"],
                        resources=["arn:aws:logs:*:409599951855:log-group:*:log-stream:*"]
                        ),
    iam.PolicyStatement(sid="EnableCreateLogs",
                        effect=iam.Effect.ALLOW,
                        actions=["logs:CreateLogStream", "logs:CreateLogGroup"],
                        resources=["arn:aws:logs:*:409599951855:log-group:*"]
                        ),
    iam.PolicyStatement(sid="S3List",
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListBucket"],
                        resources=["arn:aws:s3:::c360-tiger-analytics"]),
    iam.PolicyStatement(sid="S3Access",
                        effect=iam.Effect.ALLOW,
                        actions=["s3:putObject", "s3:getObject"],
                        resources=["arn:aws:s3:::c360-tiger-analytics/*"]),
    # Encrypted data keys from secrets manager
    iam.PolicyStatement(sid="EncryptionSecret",
                        effect=iam.Effect.ALLOW,
                        actions=["secretsmanager:GetSecretValue"],
                        resources=[
                            "arn:aws:secretsmanager:us-west-2:409599951855:secret:ww360/encryption_keys-XkdVbA",
                            "arn:aws:secretsmanager:us-west-2:409599951855:secret:tiger/ven-Jo9KLX",
                            "arn:aws:secretsmanager:us-west-2:409599951855:secret:tiger/nas-TNnrjs"
                        ]),
    # Tokenization Service Lambda functions
    iam.PolicyStatement(sid="TokenizationServiceInvoke",
                        effect=iam.Effect.ALLOW,
                        actions=["lambda:InvokeFunction"],
                        resources=[
                            "arn:aws:lambda:us-west-2:409599951855:function:TokenizerService",
                            "arn:aws:lambda:us-west-2:409599951855:function:DetokenizerService"
                        ])
]

PARAMS_ML_EC2 = {
    "name": "Enablement_TigerAnalytics_ML_EC2",  # EC2 instance name
    "instance_type": "m5a.16xlarge",  # one of https://aws.amazon.com/ec2/instance-types/
    "ami_id": "ami-054213cd4530458f0",  # Image Id to use in the EC2
    "key_name": "tiger_ec2",  # Registered key name for ssh access
    "vpc_id": "vpc-547b782c",
    "subnet_type": "PRIVATE",
    "network_rules_ingress": ml_ingress_rules,
    "disks": ml_disks,
    "policy": ML_DOCUMENT_POLICY,
}

ML_BUCKET_PARAMS = {
    "id": "MLBucket",
    "name": "c360-tiger-analytics"
}
