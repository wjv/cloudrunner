"""AWS Resource Types"""


from PseudoParameters import *


class Resource(object):

  keymap = {'Type': 'resource_type',
            'Properties': 'properties',
            'Metadata': 'metadata',
            'DependsOn': 'depends_on',
            'DeletionPolicy': 'deletion_policy'}

  def __init__(self, resource_type):
    self.resource_type = resource_type

  @property
  def template(self):
    T = {}
    for key, attrib_name in self.keymap.items():
      try:
        attrib = getattr(self, attrib_name)
      except AttributeError:
        pass
      else:
        if attrib:
          T[key] = attrib
    return T


class CFN_Init(Resource):

  """AWS::CloudFormation::Init"""

  # Is officialy a Resource Type, but doesn't quite act like one --
  # no Type attribute, no Properties, &c.
  # NOTE that generally we either contain one configset and a bunch of configs,
  # or a single config named 'config'.

  def __init__(self, template={}):
    try:
      self.configsets = template.pop('configsets')
    except KeyError:
      self.configsets = {}
    if len(template) == 0:
      self.configs = {}
    elif len(template) == 1:
      self.configs = {'config', Config(template.pop('config'))}
    else:
      self.configs = dict((k, Config(v)) for k, v in template.items())

  def __len__(self):
    # Allows truth-testing on CFNInit instance
    return len(self.configs)

  def add_config(self, name='', template={}):
    if not name and not self:
      self.add_config(name='config', template=template)
    if name in self.configs:
      raise AttributeError, "Config with name '%s' already present" % name
    self.configs[name] = Config(template)

  # configsets is a dict of lists of config _names_
  def add_configset(self, name, configlist):
    self.configsets[name] = []
    for configname in configlist:
      if config not in self.configs:
        self.add_config(configname)
      self.configsets[name].append(configname)

  @property
  def template(self):
    D = {}
    if self.configsets:
      D['configsets'] = self.configsets
    for config in self.configs:
      D['config'] = config.template
    return {'AWS::CloudFormation::Init': D}


# TODO: Integrate into new class and delete this
class IAM_Policy(Resource):

  """AWS::IAM::Policy"""

  # http://docs.amazonwebservices.com/IAM/latest/UserGuide/AccessPolicyLanguage.html
  # http://awspolicygen.s3.amazonaws.com/policygen.html
  #
  # Maybe for now just read in pre-created JSON policydocs?

  def __init__(self, name, policydoc, groups=[], users=[]):
    super(IAM_Policy, self).__init__(resource_type="AWS::IAM::Policy")
    self.properties = {}
    self.properties['PolicyName'] = name
    self.properties['PolicyDocument'] = json.loads(policydoc)
    if groups:
      self.properties['Groups'] = map(Ref, groups)
    if users:
      self.properties['Users'] = map(Ref, users)


# TODO: Integrate into new class and delete this
class IAM_User(Resource):

  """AWS::IAM::User"""

  def __init__(self, path='/', groups=[], password='', policies=[]):
    super(IAM_User, self).__init__(resource_type="AWS::IAM::User")
    self.properties = {}
    if path:
      self.properties['Path'] = path
    if groups:
      self.properties['Groups'] = groups
    if password:
      self.properties['LoginProfile'] = {"Password": password}
    if policies:
      # XXX These have to be inline; the obverse is to insert references to
      # users into IAM::Policy
      # For starters might just be best NOT to define policies here.
      self.properties['Policies'] = policies

  # See XXX above
  def addPolicy(self, policy):
    if isinsance(policy, IAM_Policy):
      policy = Ref(policy)
    try:
      self.properties['Policies'].append(policy)
    except AttributeError:
      self.properties['Policies'] = [policy]


# XXX --- XXX #

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

for type_id, required_properties in resourcetypes.items():
  class_name = type_id.replace('AWS::', '').replace('::', '_')
  globals()[class_name] = make_resourcetype(class_name, type_id,
                                            required_properties)
