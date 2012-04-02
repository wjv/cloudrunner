#!/usr/bin/env python

import json
import re
import types

from IntrinsicFunctions import *
from PseudoParameters import *

# 3rd party packages in PyPI
from bidict import bidict
import cloudformation as cfn


class Stack(object):

  def __init__(self, description="", version="2010-09-09"):
    self.description = description
    self.version = version
    self.namespace = bidict()
    self.parameters = []
    self.mappings = []
    self.resources = []

  def addParameter(self, name, p):
    assert isinstance(p, Parameter)
    self.namespace[name] = p
    self.parameters.append(p)

  def addResource(self, name, r):
    assert isinstance(r, Resource)
    self.namespace[name] = r
    self.resources.append(r)

  def dereference(self, obj):
    """Return (obj.name, obj.template) fullly resolved in Stack's namespace."""
    def _flatten(t_obj):
      if isinstance(t_obj, dict):
        return dict([(k, _flatten(v)) for (k, v) in t_obj.items()])
      elif isinstance(t_obj, list):
        return map(_flatten, t_obj)
      elif isinstance(t_obj, str):
        return t_obj
      else:
        return _flatten(t_obj.template)
    return self.namespace.inv[obj], _flatten(obj.template)

  @property
  def template(self):
    T = {"AWSTemplateFormatVersion": self.version}
    if self.description:
      T["Description"] = self.description
    if self.mappings:
      T["Mappings"] = dict(self.dereference(o) for o in self.mappings)
    if self.parameters:
      T["Parameters"] = dict(self.dereference(o) for o in self.parameters)
    if self.resources:
      T["Resources"] = dict(self.dereference(o) for o in self.resources)
    return T


class Parameter:

  def __init__(self, paramtype, description="", default=None,
               allowed_values=[], constraint_description="", no_echo=None):
    assert paramtype in ['String']
    self.template = {'Type': paramtype}
    if description:
      self.template['Description'] = description
    if default:
      self.template['Default'] = default
    if allowed_values:
      self.template['AllowedValues'] = allowed_values
    if constraint_description:
      self.template['ConstraintDescription'] = constraint_description
    if no_echo is not None:
      self.template['NoEcho'] = no_echo


class Mapping:

  # This is essentially a dictionary where every key has a bunch of named
  # values (another dict!)
  # This is very rough -- eventually reimplement as a subclass of dict?

  def __init__(self.valuenames, mapping={}):
    self.template = mapping

  def put(self, key, valuename, value):
    self.template[key][valuename] = value

  def get(self.key, valuename):
    return self.template[key][valuename]


# Utility class; will never be an attriute of Stack
class InterpolatedScript(object):

  param_regex = re.compile(r"XXX__(?P<obj>\S+)__XXX")

  def __init__(self, fh, substitutions={}):
    #substitutions is a dict of obj_name->objects
    self.lines = []
    for line in fh.readlines():
      while True:
        m = self.param_regex.search(line)
        if not m:
          self.lines.append(line)
          break
        else:
          obj = substitutions[m.groupdict()['obj']]
          first, last = m.split(line)
          self.lines.extend([first, obj])
          line = last

  @property
  def template(self):
    return self.lines


# Utility class; will never be an attriute of Stack
class Config(object):

  from string import ascii_lowercase as a_l
  cmd_indices = [c + d for c in a_l for d in a_l]
  # XXX must delete these two unless we can come up with a rdict we like
  config_keys = ['commands', 'files', 'groups', 'packages', 'services',
                 'sources', 'users']
  pkg_types = ['yum', 'python']                 # XXX expand

  def __init__(self, template={}):
    self.__dict__.update(template)              # XXX is this kosher?

  def add_package(self, pkg_type, name, versions=[]):
    if not isinstance(versions, list):
      versions = [versions]
    if not hasattr(self, 'packages'):
      self.packages = {}
    if not 'pkg_type' in self.packages:
      self.packages[pkg_type] = {}
    self.packages[pkg_type][name] = versions

  def _next_cmdprefix(self, prefix):
    return self.cmd_indices[self.cmd_indices.index(prefix) + 1]

  def add_command(self, name, command):
    """Add a command to config.

    Commands are executed in alphabetical order. Hence, we prefix command names
    with "aa_", "ab_", ...

    """
    # TODO add support for env, cwd, test, ignoreErrors
    # XXX Figure out a way that commands can have references
    assert isinstance(command, (str, list)), \
        "%s: command must be a string or list" % self.__name__
    if not hasattr(self, 'commands'):
      self.commands = {}
      prefix = 'aa'
    else:
      last_prefix = sorted(self.commands.keys())[-1].split('_')[0]
      prefix = self._next_cmdprefix(last_prefix)
    self.commands['_'.join([prefix, name])] = command

  @property
  def template(self):
    return self.__dict__                # XXX XXX XXX 

# ----------

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


class CFN_WaitCondition(Resource):

  """AWS::CloudFormation::WaitCondition"""

  def __init__(self):
    super(CFN_WaitCondition, self).__init__(resource_type="AWS::CloudFormation::WaitCondition")
    

class CFN_WaitHandle(Resource):

  """AWS::CloudFormation::WaitHandle"""

  def __init__(self):
    super(CFN_WaitHandle, self).__init__(resource_type="AWS::CloudFormation::WaitHandle")
    

class EC2_Instance(Resource):

  """AWS::EC2::Instance"""

  def __init__(self):
    super(EC2_Instance, self).__init__(resource_type="AWS::EC2::Instance")
    self.properties = {}
    self.metadata = {}


class EC2_SecurityGroup(Resource):

  """AWS::EC2::SecurityGroup"""

  def __init__(self):
    super(EC2_SecurityGroup, self).__init__( resource_type="AWS::EC2::SecurityGroup")


class IAM_AccessKey(Resource):

  """AWS::IAM::AccessKey"""

  def __init__(self):
    super(IAM_AccessKey, self).__init__(resource_type="AWS::IAM::AccessKey")


class IAM_User(Resource):

  """AWS::IAM::User"""

  def __init__(self):
    super(IAM_User, self).__init__(resource_type="AWS::IAM::User")

# ----------

# High-level class
class EC2Instance(EC2_Instance):

  def __init__(self, image_id, keypair, instance_type, userdata_files=[],
               userdata_script_fh=None, cfn_init=CFN_Init(),
               security_groups=[], tags=[]):

    super(EC2Instance, self).__init__()

    self.properties['InstanceType'] = instance_type
    self.properties['ImageId'] = image_id
    self.properties['KeyPair'] = Ref(keypair)
    self.properties['Metadata'] = cfn_init

    if security_groups:
      self.properties['SecurityGroups'] = security_groups
    else:
      self.properties['SecurityGroups'] = ['default']

    if tags:
      self.properties['Tags'] = tags

    # userdata_files takes precedence over userdata_script
    if userdata_files:
      self.properties['UserData'] = self._format_userdata(userdata_files)
    elif userdata_script_fh:
      userdata_script = InterpolatedScript(userdata_script_fh)
      self.properties['UserData'] = \
          Fn_Base64(Fn_Join('', userdata_script.template))

    self.cfn_config = {}
    self.metadata["AWS::CloudFormation::Init"] = {"config": self.cfn_config}

  def addPackage(pkg_type, pkg_name, version_list=[]):
    assert pkg_type in ['yum', 'python', 'ruby']
    pkg_dict = self.cfn_config.setdefault('packages', {})
    pkg_type_dict = pkg_dict.setdefault(pkg_type, {})
    pkg_type_dict[pkg_name] = version_list

  def addService(service_type, service_name, enabled=True, ensure_running=True):
    assert service_type in ['sysvinit']
    srv_dict = self.cfn_config.setdefault('services', {})
    srv_type_dict = srv_dict.setdefault(service_type, {})
    srv_type_dict[service_name] = {'enabled': str(enabled).lower(),
                                   'ensureRunning': str(ensure_running).lower()}

  def addCommand(name, command, test='', env={}, ignore_errors=None):
    commands_dict = self.cfn_config.setdefault('commands', {})
    cmd_dict = commands_dict[name] = {'command': command}
    if test:
      cmd_dict['test'] = test
    if env:
      cmd_dict['env'] = env
    if ignore_errors is not None:
      cmd_dict['ignoreErrors'] = ignore_errors.__repr__().lower()

  def _populate_userdata(self, files):
    if len(files) == 1:
      return {'Fn::Base64': file2cfn(files[0])}
    else:
      pass # mess with MIME


def jsonify(obj, indent=2, *args, **kwargs):
  return json.dumps(obj.template, indent=indent, *args, **kwargs)
