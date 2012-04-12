"""AWS Resource Property Types"""


class ResourcePropertyType(object):

  @property
  def template(self):
    return self.Properties

class LoginProfile(object):

  # Embedded property of AWS::IAM::User

  def __init__(self, Password=''):
    self.Password = Password

  @property
  def template(self):
    return {"Password": self.Password}
  

class EC2SecurityGroupRule(ResourcePropertyType):

  # XXX anything in stdlib for handling IP addresses &c.?

  def __init__(self, ip_protocol, from_port, to_port, cidr_ip='',
               sourcegroup=''):
    self.Properties = {}
    self.Properties['IpProtocol'] = ip_protocol
    self.Properties['FromPort'] = from_port
    self.Properties['ToPort'] = to_port
    if sourcegroup:
      self.Properties['SourceSecurityGroupName'] = sourcegroup
    else:
      self.Properties['CidrIp'] = cidr_ip
