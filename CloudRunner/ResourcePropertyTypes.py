"""AWS Resource Property Types"""


class ResourceProperty(object):

  @property
  def template(self):
    return self.properties


class EC2SecurityGroupRule(ResourceProperty):

  # XXX anything in stdlib for handling IP addresses &c.?

  def __init__(self, ip_protocol, from_port, to_port, cidr_ip='',
               sourcegroup=''):
    self.properties = {}
    self.properties['IpProtocol'] = ip_protocol
    self.properties['FromPort'] = from_port
    self.properties['ToPort'] = to_port
    if sourcegroup:
      self.properties['SourceSecurityGroupName'] = sourcegroup
    else:
      self.properties['CidrIp'] = cidr_ip
