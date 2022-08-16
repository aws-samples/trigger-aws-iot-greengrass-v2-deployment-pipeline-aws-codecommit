script = ''' \
#! /bin/bash
sudo yum install java-11-amazon-corretto

curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip

unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && rm greengrass-nucleus-latest.zip

sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
  -jar ./GreengrassInstaller/lib/Greengrass.jar \
  --aws-region region \
  --thing-name {CoreDeviceName} \
  --thing-group-name {CoreDeviceGroupName} \
  --thing-policy-name {ProjectPrefix}GreengrassV2IoTThingPolicy \
  --tes-role-name {TokenExchangeRoleName} \
  --tes-role-alias-name {TokenExchangeRoleAlias} 
  --component-default-user ggc_user:ggc_group \
  --provision true \
  --setup-system-service true

'''