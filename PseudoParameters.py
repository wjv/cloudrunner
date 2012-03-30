"""AWS CloudFormation pseudo parameters"""


__all__ = ['region', 'stackname']


class PseudoParameter(object):

  @property
  def template(self):
    return {"Ref": self.name}


class AWSRegion(PseudoParameter):

  def __init__(self):
    self.name = "AWS::Region"


class AWSStackName(PseudoParameter):

  def __init__(sel):
    self.name = "AWS::StackName"


region = AWSRegion()
stackname = AWSStackName()
