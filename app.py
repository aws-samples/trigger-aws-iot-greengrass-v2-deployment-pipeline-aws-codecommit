#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ggv2_cdk_gdk_python.ggv2_cdk_gdk_python_stack import Ggv2CdkGdkPythonStack


app = cdk.App()
Ggv2CdkGdkPythonStack(
    app,
    "Ggv2CdkGdkPythonStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region"),
    ),
)

app.synth()
