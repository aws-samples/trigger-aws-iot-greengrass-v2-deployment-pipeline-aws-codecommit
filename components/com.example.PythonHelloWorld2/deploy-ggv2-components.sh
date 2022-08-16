#!/bin/bash
# /*
# __author__ = "Srikanth Kodali"
# edited = "Jack Tanny and Joyson Neville Lewis "
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# */

# MUST BE RUN AS ROOT
# MUST FIRST PASS DEV_IOT_THING / DEV_IOT_THING_GROUP AND AWS_ACCOUNT_NUMBER TO THE SCRIPT WHEN RUNNING IT
# MUST INSTALL SIGIL 
# Purpose: This bash script deploys an AWS IoT Greengrass component to AWS IoT Thing(s) which are a part of an AWS IoT Thing Group. The script takes inputs such as the component artifacts, recipe template, and configuration details, and then creates the component and deploys it on the Thing(s). 
# Pre-Requisites: Greengrass must be installed on the edge device, the component artifact files must be in the SRC_FOLDER on the Linux machine running this script, and a recipe-file-template.yaml file must exist on the Linux machine for the component you are creating and deploying. One of the best ways to accomplish this is to clone the repository where these items are kept, or pull recent changes/updates if the repository is already cloned on the Linux machine you are using.

# This version has been adapted to run in code deploy on a linux 2 ubuntu instance. 

# Here you can set environment variables 
_setEnv()
{
  AWS="aws"
  # Set either the AWS Greengrass Thing or Thing Group in which you are deploying a component 
  #### WHEN SWITCHING BETWEEN USING THIS SCRIPT FOR THINGS, AND THING GROUPS, CHECK THAT EACH FUNCTION CALLS THE CORRECT DEV_IOT_THING* VARIABLE. I suggest using ctrl+f for this check. 
  echo "DEV_IOT_THING_GROUP: ${DEV_IOT_THING_GROUP}" # the Greengrass Thing group which you want to deploy a component to. All Things in Thing Group will get component. 
  # echo "DEV_IOT_THING: ${DEV_IOT_THING}" # the Greengrass Thing you want to deploy a component on 
  echo "AWS_ACCOUNT_NUMBER: ${AWS_ACCOUNT_NUMBER}"
  #echo "NEXT_VERSION: ${NEXT_VERSION}"
  echo "AWS_REGION: ${AWS_REGION}"
  echo "COMPONENT_NAME: ${COMPONENT_NAME}"
  echo "CODE_BUILD_ROLE_ARN: ${CODE_BUILD_ROLE_ARN}"
  AWS_REGION=${AWS_REGION}
  START_VERSION_NUMBER="1.0.0" # Set the first version of the component here
  DEPLOYMENT_CONFIG_FILE="deployment_configuration.json"
  export AWS_DEFAULT_REGION=${AWS_REGION}
  
}


# jq is a Linux command line utility that is easily used to extract data from JSON documents. 
_check_if_jq_exists() {
  JQ=`which jq`
  if [ $? -eq 0 ]; then # checking if JQ (represented by $?) exists
    echo "JQ exists."
  else
    echo "jq does not exists, please install it."
    apt-get install jq -y
    exit 1;
  fi
}




# This function creates the configuration file. It is passed the DEPLOY_FILE_ARG argument, which serves as the name of the configuration file returned
# by the function. The COMP_NAME is the second argument, which serves as the componentName. For more information about this configuration file, see
# https://docs.aws.amazon.com/greengrass/v2/developerguide/gdk-cli-configuration-file.html
# If the deployment exists for the DEV_IOT_THING or DEV_IOT_THING_GROUP, the CURRENT_VERSION_NUMBER is incremented to the new version. Otherwise, the CURRENT_VERSION_NUMBER set in the _setEnv() is used as the current version. 
# This function also returns the NEXT_VERSION variable to be used when creating the new recipe file 
_prepare_deployment_config_file_based_on_deployment_name()
{
  DEPLOY_FILE_ARG=$1
  COMP_NAME=$2
  START_VERSION=$3
  AWS_REGION=$4
  COMP_VERSION=""
  
  THING_GROUP_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUMBER}:thinggroup/${DEV_IOT_THING_GROUP}"
  deployment_id=`aws greengrassv2 list-deployments --region ${AWS_REGION} --target-arn ${THING_GROUP_ARN} | jq -r '.deployments[]' | jq -r .deploymentId`

  echo "Deployment Id is : ${deployment_id}"

  ### Check if the component was created previously and used in other thing groups.

  EXITING_COMP_VERSION=`aws greengrassv2 list-components --region ${AWS_REGION} | jq -r '.components[] | select(.componentName == "'"${COMP_NAME}"'").latestVersion' | jq -r '.componentVersion'` # any component with COMP_NAME
  echo "Existing comp version is : ${EXITING_COMP_VERSION}" 
  CURRENT_VERSION_NUMBER=${EXITING_COMP_VERSION}

  if [ -z "${deployment_id}" ] || [  "${deployment_id}" = "null" ]; then # checks if the deployment ID exists for the DEV_IOT_THING_GROUP by checking if deployment_id is an empty string yes
    echo "There is no deployment for this thinggroup : ${DEV_IOT_THING_GROUP} yet."

    STR1='{"'
    STR2=${COMP_NAME}
    STR3='": {"componentVersion": '
    STR4=${CURRENT_VERSION_NUMBER}
    STR5=',"configurationUpdate":{"reset":[""]}}}' # resets the configuration in the deployment so it will not re-use the old configuration and instead use the default configuration we set 
    NEW_CONFIG_JSON=$STR1$STR2$STR3\"$STR4\"$STR5 # composes a NEW_CONFIG_JSON, following the GDK CLI file format https://docs.aws.amazon.com/greengrass/v2/developerguide/gdk-cli-configuration-file.html#:~:text=configuration%20file%20examples-,GDK%20CLI%20configuration%20file%20format,-When%20you%20define
    echo ${NEW_CONFIG_JSON}
    NEXT_VERSION=${CURRENT_VERSION_NUMBER}
  else # if deployemnt ID exists already

    NEW_CONFIG_JSON=`aws greengrassv2 get-deployment --region ${AWS_REGION} --deployment-id ${deployment_id} | jq .'components' | jq 'del(."$COMP_NAME")' | jq  '. += {"'"$COMP_NAME"'": {"componentVersion": "'"$CURRENT_VERSION_NUMBER"'","configurationUpdate":{"reset":[""]}}}'` # compose a NEW_CONFIG_JSON, following the GDK CLI file format, using the NEXT_VERSION returned from _getNextVersion 2 lines above 
  fi
  FINAL_CONFIG_JSON='{"components":'$NEW_CONFIG_JSON'}'
  echo $(echo "$FINAL_CONFIG_JSON" | jq '.') > ${DEPLOY_FILE_ARG} # creates DEPLOY_FILE_ARG file, named as the first argument passed to the functon, comprised of the contents of the FINAL_CONFIG_JSON variable
  cat ${DEPLOY_FILE_ARG} | jq # displays contents of the configuration file
}

# this function simply deploys the configuration to all things in the DEV_IOT_THING_GROUP
_deploy_configuration_on_devices() 
{
  echo "ARN is in deployment : ${ARN}"
  CONFIG_FILE_ARG=$1
  CONFIG_URI="fileb://${CONFIG_FILE_ARG}"
  # If using a THING_GROUP, uncomment the below line, and comment out the line after it. 
  THING_GROUP_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUMBER}:thinggroup/${DEV_IOT_THING_GROUP}"
  #THING_ARN="arn:aws:iot:${AWS_REGION}:${AWS_ACCOUNT_NUM}:thing/${DEV_IOT_THING}"
  RES=`${AWS} greengrassv2 create-deployment --target-arn ${THING_GROUP_ARN} --deployment-name test --cli-input-json ${CONFIG_URI} --region ${AWS_REGION} --deployment-policies failureHandlingPolicy=DO_NOTHING`
  echo ${RES}
}

########################## MAIN ###############################
#
###############################################################
DEV_IOT_THING_GROUP=${1}
AWS_ACCOUNT_NUMBER=${2}
AWS_REGION=${3}
COMPONENT_NAME=${4}


include_public_comps=true
_setEnv
_check_if_jq_exists
_prepare_deployment_config_file_based_on_deployment_name ${DEPLOYMENT_CONFIG_FILE} ${COMPONENT_NAME} ${START_VERSION_NUMBER} ${AWS_REGION} # creates the configuration file, named DEPLOYMENT_CONFIG_FILE, with the ComponentName as COMPONENT_NAME
_deploy_configuration_on_devices ${DEPLOYMENT_CONFIG_FILE} # deploys component using configuration file on all things in the DEV_IOT_THING_GROUP