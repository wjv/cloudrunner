#!/usr/bin/env python

import json
from cfntools import *

S = Stack()

pKeyName = Parameter(paramtype='String', description="EC2 key pair")

C = Config()
C.add_command("list files", "ls -al")
C.add_package("yum", "gcc")


myconfig = Config()
myconfig.add_package('yum', 'gcc')
cfn_init = CFNInit()
cfn_init.add_config(myconfig)
myInstance = EC2Instance(image_id="ABI-abc", keypair=pKeyName,
                         instance_type="foo.small", cfn_init=cfn_init)


S.addParameter("pKeyName", pKeyName)
S.addResource("myInstance", myInstance)


print json.dumps(S.template, indent=2)
