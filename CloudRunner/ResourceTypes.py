"""AWS Resource Types"""


resourcetypes = {
  "AWS::CloudFormation::WaitCondition": ["Handle", "Timeout"],
  "AWS::CloudFormation::WaitConditionHandle": [],
  "AWS::EC2::Instance": ["ImageId"],
  "AWS::EC2::SecurityGroup": ["GroupDescription"],
  "AWS::IAM::AccessKey": ["UserName"],
  "AWS::IAM::Policy": ["PolicyName", "PolicyDocument"],
  "AWS::IAM::User": [],
  "AWS::IAM::UserToGroupAddition": ["Group", "Users"]
}


class ResourceType(object):

  resource_attributes = ['Type',
                         'Properties',
                         'Metadata',
                         'DependsOn',
                         'DeletionPolicy']

  def __init__(self,
               Properties={}, Metadata={}, DependsOn={}, DeletionPolicy={},
               template={}):
    if template: # XXX needs work if to be used
      for key in self.resource_attributes:
        self.__dict__[key] = template[key]
    else:
      self.Properties = Properties
      self.Metadata = Metadata
      self.DependsOn = DependsOn
      self.DeletionPolicy = DeletionPolicy

  @property
  def template(self):
    return dict((k, v) for k, v in self.__dict__.items()
                if v and k in self.resource_attributes)


def make_init(resource_type, required_properties):
  def i(self, *args, **kwargs):
    self.Type = resource_type
    args = list(args)
    properties = {}
    for p in required_properties:
      if 'Properties' in kwargs and p in kwargs['Properties']:
        pass
      elif p in kwargs:
        properties[p] = kwargs[p]
        del kwargs[p]
      else:
        try:
          properties[p] = args.pop(0)
        except IndexError:
          raise TypeError, '"%s" requires property "%s"' % (resource_type, p)
    ResourceType.__init__(self, *args, **kwargs)
    self.Properties.update(properties)
  i.__name__ = '__init__'
  return i

def make_resourcetype(class_name, type_id, required_properties):
  return type(class_name, (ResourceType,),
              {'__init__': make_init(type_id, required_properties),
               '__doc__': type_id})

__all__ = []

for type_id, required_properties in resourcetypes.items():
  class_name = type_id.replace('AWS::', '').replace('::', '_')
  globals()[class_name] = make_resourcetype(class_name, type_id,
                                            required_properties)
  __all__.append(class_name)

from Config import CloudFormation_Init
__all__.append("CloudFormation_Init")
