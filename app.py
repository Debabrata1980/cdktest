#!/usr/bin/env python3

import aws_cdk as cdk

import JSON

from cdkstack.cdkstack import CdkStack
from params  import STACK_NAME, PARAMS, PARAMS_ML_EC2, ML_BUCKET_PARAMS, ACCOUNT, REGION, TAGS


app = cdk.App()
stack= CdkStack(app, "cdkstack",account=ACCOUNT, region=REGION, tags=TAGS, params=PARAMS)
#stack.define_rds(PARAMS)


app.synth()
