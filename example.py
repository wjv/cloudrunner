#!/usr/bin/env python

import json
from cfntools import *

S = Stack()

pKeyName = Parameter(paramtype='String', description="EC2 key pair")

myInstance = EC2Instance(image_id="ABI-abc", key=pKeyName,
                         instance_type="foo.small")

S.addParameter("pKeyName", pKeyName)
S.addResource("myInstance", myInstance)

print json.dumps(S.template, indent=2)
