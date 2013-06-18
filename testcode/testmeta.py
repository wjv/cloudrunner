resourcetypes = \
"""
EC2Instance     AWS::EC2::Instance      ImageId
"""

class Resource(object):

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
    Resource.__init__(self, *args, **kwargs)
    self.Properties.update(properties)
  i.__name__ = '__init__'
  return i

def make_resourcetype(name, type_id, required_properties):
  return type(name, (Resource,), {'__init__':
                                  make_init(type_id, required_properties)})

EC2Instance = make_resourcetype("EC2Instance", "AWS::EC2::Instance",
                                ["ImageId"])
