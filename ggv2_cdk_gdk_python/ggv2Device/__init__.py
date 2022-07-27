#  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#  SPDX-License-Identifier: MIT-0

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
#from aws_cdk import core
import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_iam as iam,
    aws_codecommit as codecommit,
    aws_ec2 as ec2,
)
#importing the script
from constructs import Construct
class GGv2Device(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, accountID,regionAWS,**kwargs) -> None:
         #output all parameters
        params = kwargs.pop('params')
        super().__init__(scope, construct_id,**kwargs)
       

        
        project_prefix = str(accountID)
        core_device_name = str(params.get("coreDeviceName"))
        core_device_group_name = str(params.get("coreDeviceGroupName"))

        # Greengrass Token Exchange Role Names
        token_exchange_role_name = "role/{}GreengrassV2TokenExchangeRole".format(project_prefix)
        token_exchange_policy_name_ = "policy/{}GreengrassV2TokenExchangeRoleAccess".format(project_prefix)

        token_exchange_role_arn = "arn:aws:iam::{}:{}".format(accountID, token_exchange_role_name)
        token_exchange_policy_arn = "arn:aws:iam::{}:{}".format(accountID, token_exchange_policy_name_)
        # Create Greengrass Installer
        installer_role_name = "{}GreengrassV2InstallerRole".format(project_prefix)
        installer_policy_name = "{}GreengrassV2InstallerPolicy".format(project_prefix)
        

        installer_iam_policy_statement =  iam.PolicyDocument(statements=[
            iam.PolicyStatement(
            actions=[ "iam:AttachRolePolicy",
                "iam:CreatePolicy",
                "iam:CreateRole",
                "iam:GetPolicy",
                "iam:GetRole",
                "iam:PassRole"
                         ],
                sid="CreateTokenExchangeRole",         
                effect=iam.Effect.ALLOW,
                resources=[
                    token_exchange_role_arn,
                    token_exchange_policy_arn
                ]),
                iam.PolicyStatement(
                actions=[ "iam:AttachRolePolicy",
                "iot:AddThingToThingGroup",
                "iot:AttachPolicy",
                "iot:AttachThingPrincipal",
                "iot:CreateKeysAndCertificate",
                "iot:CreatePolicy",
                "iot:CreateRoleAlias",
                "iot:CreateThing",
                "iot:CreateThingGroup",
                "iot:DescribeEndpoint",
                "iot:DescribeRoleAlias",
                "iot:DescribeThingGroup",
                "iot:GetPolicy"
                         ],
                sid="CreateIoTResources",         
                effect=iam.Effect.ALLOW,
                resources=["*"]
                ),
                iam.PolicyStatement(
                actions=[ "greengrass:CreateDeployment",
                "iot:CancelJob",
                "iot:CreateJob",
                "iot:DeleteThingShadow",
                "iot:DescribeJob",
                "iot:DescribeThing",
                "iot:DescribeThingGroup",
                "iot:GetThingShadow",
                "iot:UpdateJob",
                "iot:UpdateThingShadow",
                "s3:*"
                         ],
                sid="DeployDevTools",         
                effect=iam.Effect.ALLOW,
                resources=["*"]
                )
        ])
    # Greengrass Installer role (change the role name if you need)
        greengrass_installer_role = iam.Role(
            self, 'greengrassInstallerRole',
            assumed_by=iam.CompositePrincipal(iam.ServicePrincipal("greengrass.amazonaws.com"),iam.ServicePrincipal("ec2.amazonaws.com")),
            role_name=installer_role_name,
            inline_policies={installer_policy_name:installer_iam_policy_statement}
        )
        greengrass_installer_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="AmazonSSMManagedInstanceCore"))

        var_replace = {
            "CoreDeviceName": core_device_name,
            "CoreDeviceGroupName": core_device_group_name,
            "ProjectPrefix": project_prefix,
            "TokenExchangeRoleName": token_exchange_role_name.replace("role/",""),
            "TokenExchangeRoleAlias": str(token_exchange_role_name.replace("role/","")+"Alias"),
            "Region":regionAWS
        }
        script = ''' sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE  -jar ./GreengrassInstaller/lib/Greengrass.jar --aws-region {Region} --thing-name {CoreDeviceName} --thing-group-name {CoreDeviceGroupName} \
            --thing-policy-name {ProjectPrefix}GreengrassV2IoTThingPolicy\
            --tes-role-name {TokenExchangeRoleName}\
            --tes-role-alias-name {TokenExchangeRoleAlias}\
            --component-default-user ggc_user:ggc_group\
            --provision true\
            --setup-system-service true'''

        user_data_script = script.format(**var_replace)
        user_data = ec2.UserData.for_linux(shebang="#!/bin/bash")
        user_data.add_commands("echo test")
        #user_data.add_commands('until git clone https://github.com/aws-quickstart/quickstart-linux-utilities.git; do echo "Retrying"; done',
        #    "cd /quickstart-linux-utilities",
        #    "source quickstart-cfn-tools.source",
        #    "qs_update-os || qs_err",
        #    "qs_bootstrap_pip || qs_err",
        #    "qs_aws-cfn-bootstrap || qs_err",
        #    "mkdir -p /opt/aws/bin",
        #    "ln -s /usr/local/bin/cfn-* /opt/aws/bin/"
        #    )
       
        linux_machine_image = ec2.MachineImage.latest_amazon_linux(cached_in_context=False,user_data=user_data,generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)
        vpc = ec2.Vpc.from_lookup(self,"Vpc",is_default=True)
        security_group = ec2.SecurityGroup(self,"GGSecurityGroup",vpc=vpc,allow_all_outbound=True)
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(),ec2.Port.tcp(8883))
        security_group.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc_cidr_block),ec2.Port.tcp(443))
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(),ec2.Port.tcp(443))
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(),ec2.Port.tcp(80))


        instanceType=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2,ec2.InstanceSize.LARGE)
        

        ggv2CoreDevice = ec2.Instance(self,"ggv2CoreDevice",instance_name=str(accountID)+project_prefix+"- GGv2Instance",
                        machine_image=linux_machine_image,vpc=vpc, security_group=security_group,instance_type=instanceType,
                        role=greengrass_installer_role,
                        init=ec2.CloudFormationInit.from_elements(
                                ec2.InitCommand.shell_command("sudo -E yum install -y aws-cfn-bootstrap"),
                                ec2.InitCommand.shell_command("sudo yum update -y && sudo -E yum install java-11-amazon-corretto -y"),
                                #ec2.InitCommand.shell_command("sudo dnf install python3"),
                                ec2.InitCommand.shell_command("curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip"),
                                ec2.InitCommand.shell_command("unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && rm greengrass-nucleus-latest.zip"),
                                ec2.InitCommand.shell_command(user_data_script)


                        ))   
        

