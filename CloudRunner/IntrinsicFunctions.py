"""AWS CloudFormation Intrinsic Functions"""

__all__ = ['Fn_Join', 'Fn_Base64', 'Fn_GetAtt', 'Ref']


class IntrinsicFunction(object):
  pass


class Fn_Base64(IntrinsicFunction):

  def __init__(self, obj):
    self.obj = obj

  @property
  def template(self):
    return {"Fn:Base64": self.obj}


class Fn_FindInMap(IntrinsicFunction):

  def __init__(self, mapname, key, value):
    self.mapname = mapname
    self.key = key
    self.value = value

  @property
  def template(self):
    return {"Fn::FindInMap": [self.mapname, self.key, self.value]}


class Fn_GetAtt(IntrinsicFunction):

  def __init__(self, obj, attrib_name):
    # obj is the actual object; attrib is the attribute *name*
    self.obj = obj
    self.attrib_name = attrib_name

  @property
  def template(self):
    return {"Fn::GetAtt": [self.obj, self.attrib_name]}


class Fn_GetAZs(IntrinsicFunction):

  def __init__(self, region=""):
    self.region = region

  @property
  def template(self):
    return {"Fn::GetAZs": self.region}


class Fn_Join(IntrinsicFunction):

  def __init__(self, separator, lst):
    self.separator = separator
    self.lst = lst

  @property
  def template(self):
    return {"Fn::Join": [self.separator, self.lst]}


class Ref(IntrinsicFunction):
  
  def __init__(self, obj):
    self.obj = obj

  @property
  def template(self):
    try:
      return self.obj.reference
    except AttributeError:
      return {"Ref": self.obj}
