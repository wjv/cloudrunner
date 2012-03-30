"""AWS CloudFormation Intrinsic Functions"""

__all__ = ['Fn_Join', 'Fn_GetAtt', 'Ref']

# The idea is now that an IntrinsicFunction instance may be created anywhere,
# but can only be resolve()'d inside a Stack. Possibly the resolve() method
# should be added to all parameters &c., so that a Stack can simply do a
# recursive resolve() on any object.

class IntrinsicFunction(IntrinsicFunction):

  def resolve(self, namespace):
    # Should we pass namespace here, or just leave it for those IFuncs that
    # contain refs to override resolve() i.t.o. its params as well?
    return self.template


class Fn_Join(IntrinsicFunction):

  def __init__(self):
    self.template = {"Fn::Join", [sep, lst]}


class Fn_GetAtt(IntrinsicFunction):

  def __init__(self, obj, attrib):
    # obj is the actual object; attrib is the attribute *name*
    self.obj = obj
    self.attrib = attrib
    #self.template = {"Fn::GetAtt": [self.obj, self.attrib]}

  def resolve(self, namespace):
    # Maybe this should just BE the template property?
    return {"Fn::GetAtt": [namespace.inv[self.obj], self.attrib]}


class Ref(IntrinsicFunction):
  
  def __init__(self, obj):
    self.obj = obj

  def resolve(self, namespace):
    return {"Ref": namespace.inv[obj]}
