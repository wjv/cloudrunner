"""AWS CloudFormation Intrinsic Functions"""

__all__ = ['Fn_Join', 'Fn_GetAtt', 'Ref']


class IntrinsicFunction(object):
  pass


class Fn_Join(IntrinsicFunction):

  def __init__(self, separator, lst):
    self.separator = sep
    self.lst = lst

  @property
  def template(self):
    return {"Fn::Join", [sep, lst]}


class Fn_GetAtt(IntrinsicFunction):

  def __init__(self, obj, attrib_name):
    # obj is the actual object; attrib is the attribute *name*
    self.obj = obj
    self.attrib_name = attrib_name

  @property
  def template(self):
    return {"Fn::GetAtt": [self.obj, self.attrib_name]}


class Ref(IntrinsicFunction):
  
  def __init__(self, obj):
    self.obj = obj

  @property
  def template(self):
    return {"Ref": self.obj}
