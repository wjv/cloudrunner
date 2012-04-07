#!/bin/bash

function error_exit {
  /opt/aws/bin/cfn-signal -e 1 -r "$1" 'XXX__WAITHANDLE__XXX'
  exit 1
}

yum -y update aws-cfn-bootstrap || error_exit 'Failed to update aws-cfn-bootstrap'

AWS_CREDENTIALS=~ec2-user/.aws-credentials
echo "AWSAccessKeyId=XXX__ACCESSKEY__XXX\nAWSSecretKey=XXX__SECRETKEY__XXX" >${AWS_CREDENTIALS} && chown ec2-user:ec2-user ${AWS_CREDENTIALS} || error_exit "Failed to create ~ec2-user/.aws-credentials"

function run_configset {
  /opt/aws/bin/cfn-init -c $1 -f ${AWS_CREDENTIALS} -r EC2Instance -s XXX__STACKNAME__XXX --region XXX__AWSREGION__XXX || error_exit "Failed $1"
  /opt/aws/bin/cfn-signal -r "Success: $1" -e $? XXX__WAITHANDLE__XXX
}

for myinit in pre-init init post-init; do run_init(myinit); done

/opt/aws/bin/cfn-init -c run-app -f ${AWS_CREDENTIALS} -r EC2Instance -s XXX__STACKNAME__XXX --region XXX__AWSREGION__XXX
