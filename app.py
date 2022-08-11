#!/usr/bin/env python3

import aws_cdk as cdk

from rdscdk.rdscdk_stack import RdscdkStack


app = cdk.App()
RdscdkStack(app, "rdscdk")

app.synth()
