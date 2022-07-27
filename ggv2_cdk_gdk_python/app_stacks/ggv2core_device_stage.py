# Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
# Licensed under the Amazon Software License  http://aws.amazon.com/asl/

import aws_cdk as cdk
from constructs import Construct

from ggv2_cdk_gdk_python.app_stacks.greengrass_components_stack import (
    GreengrassComponentsStack,
)

from ggv2_cdk_gdk_python.app_stacks.monitoring_stack import (
    MonitoringStack,
)

from ggv2_cdk_gdk_python.ggv2Device import GGv2Device

class Ggv2CdkGdkCoreStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        params = {
            "createCoreDevice": self.node.try_get_context("create_core_device"),
            "coreDeviceGroupName": self.node.try_get_context("core_device_group_name"),
            "coreDeviceName": self.node.try_get_context("core_device_name"),
            "accountNumber": self.node.try_get_context("account"),
            "region": self.node.try_get_context("region"),
            "repository_arn": self.node.try_get_context("codecommit_repository_arn"),
            "project_prefix": self.node.try_get_context("project_prefix")
        }

        GGv2Device(self,"ggv2CoreDevice",accountID=self.account,regionAWS=self.region,params=params)
