#!/usr/bin/env python

from StringIO import StringIO

from CloudRunner.CloudFormation import *
from CloudRunner.Config import InterpolatedScript, Config
from CloudRunner import CFN_JSONEncoder, CFN_JSONDecoder
from CloudRunner.Library import EC2Instance

myscript = StringIO("""#!/bin/bash

echo "Hello"
echo 'World!'
""")

S = Stack()

# parameters
pKeyName = Parameter(paramtype='String', description="EC2 key pair")

# stack
policy_doc = CFN_JSONDecoder().decode(
"""{
  "Statement" : [
    {
      "Effect" : "Allow",
      "Action" : "cloudformation:DescribeStackResource",
      "Resource" : "*"
    }
  ]
}""")

root_policy = ResourceTypes.IAM_Policy("root", policy_doc)

C = Config()
C.add_command("list files", "ls -al")
C.add_package("yum", "gcc")


myconfig = Config()
myconfig.add_package('yum', 'gcc')
cfn_init = ResourceTypes.CloudFormation_Init()
cfn_init.add_config(myconfig)
myInstance = EC2Instance(image_id="ABI-abc", keypair=pKeyName,
                         instance_type="foo.small", cfn_init=cfn_init,
                         userdata_script_fh=myscript)


S.addParameter("pKeyName", pKeyName)
S.addResource("myInstance", myInstance)
S.addResource("UserPolicy", root_policy)


Encoder = CFN_JSONEncoder(indent=2)
print Encoder.encode(S.template)
