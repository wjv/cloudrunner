#!/usr/bin/env python

import re
import types

from rdict import rdict

import json
from bidict import bidict
import cloudformation as cfn

def fn_join(sep, lst):
  return {'Fn:Join': [sep, lst]}

def fn_getatt(parameterised_object):
  # takes "object[parameter]"
  regex = re.compile(r'(?P<object>[^[]+)\[(?P<parameter>\w+)\]')
  g = regex.match(parameterised_object).groupdict()
  return {"Fn:GetAtt": [g['object'], g['parameter']]}


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

psvar_region = AWSRegion()
psvar_stackname = AWSStackName()

# XXX We need a class that can encapsulate a string that contains references

# XXX Does this work for us?
# Any object not flattened to a template repr. by a class' template property
# will be flattened to a Ref by the Stack object, which contains the master
# name<->object mapping.

class Stack(object):

  def __init__(self, description="", version="2010-09-09"):
    self.description = description
    self.version = version
    self.namespace = bidict()
    self.parameters = []
    self.mappings = []
    self.resources = []
    self.name = AWSStackName()
    self.region = AWSRegion()

  def addParameter(self, name, p):
    assert isinstance(p, Parameter)
    self.namespace[name] = p
    self.parameters.append(p)

  def addResource(self, name, r):
    assert isinstance(r, Resource)
    self.namespace[name] = r
    self.resources.append(r)

  # The whole "flatteing" procedure probably ought to be devolved to the
  # various classes?  I.e. each returns a template that's simply a construct of
  # dicts, lists, strings.
  # But wait! object->name mappings only live in Stack, so maybe not?

  def _dereference(self, obj):
    """Return the name of obj in the Stack's namespace."""
    return self.namespace.inv[obj]

  def _flatten(self, obj):
    """Resolve all references in a template."""
    if isinstance(obj, dict):
      return dict([(k, self._flatten(v)) for (k, v) in obj.items()])
    elif isinstance(obj, list):
      return map(self._flatten, obj)
    elif isinstance(obj, str):
      return obj
    else:
      return {'Ref': self._dereference(obj)}

  def _templatify(self, obj_list):
    return dict([(self._dereference(o), self._flatten(o.template))
                 for o in obj_list])

  @property
  def template(self):
    T = {"AWSTemplateFormatVersion": self.version}
    if self.description:
      T["Description"] = self.description
    if self.mappings:
      T["Mappings"] = self._templatify(self.mappings)
    if self.parameters:
      T["Parameters"] = self._templatify(self.parameters)
    if self.resources:
      T["Resources"] = self._templatify(self.resources)
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
  pass

# Utility class; will never be an attriute of Stack
class InterpolatedScript(object):

  # We're going with XXX__OBJECT__XXX being {'Ref': 'OBJECT'}
  # and XXX__OBJECT[PARAM]__XXX being {'Fn::GetAtt' : ['OBJECT', 'PARAM']}

  param_regex = re.compile(r"XXX__(?P<obj>\S+)__XXX")

  def __init__(self, fh, substitutions={}):
    self.lines = []
    for line in fh.xreadlines():
      while 1:
        m = param_regex.search(line)
        if not m:
          self.lines.append(line)
          break
        else:
          obj = m.groupdict()['obj']    # XXX needs a deref
          first, last = m.split(line)
          self.lines.extend([first, obj])
          line = last

  @property
  def template(self):
    return self.lines


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


# Utility class; will never be an attriute of Stack
class CFNInit(Resource):

  # Is officialy a Resource Type, but doesn't quite act like one --
  # no Type attribute, no Properties, &c.
  # NOTE that generally we either contain one configset and a bunch of configs,
  # or a single config named 'config'.

  def __init__(self, template={}):
    try:
      self.configsets = template.pop('configsets')
    except KeyError:
      self.configsets = {}
    if not template:
      self.configs = {'config': Config()} # XXX
    elif len(template) == 1:
      self.configs = {'config', Config(template.pop('config'))}
    else:
      self.configs = dict((k, Config(v)) for k, v in template.items())

  def add_config(self, name, template={}):
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
    

class BaseInstance(Resource):

  def __init__(self):
    super(BaseInstance, self).__init__(resource_type='AWS::EC2::Instance')
    self.properties = {}
    self.metadata = {}


class EC2Instance(BaseInstance):

  def __init__(self, image_id, keypair, instance_type, userdata_files=[],
               userdata_script='', security_groups=[], tags=[]):

    super(EC2Instance, self).__init__()

    self.properties['InstanceType'] = instance_type
    self.properties['ImageId'] = image_id
    self.properties['KeyPair'] = keypair

    if security_groups:
      self.properties['SecurityGroups'] = security_groups
    else:
      self.properties['SecurityGroups'] = ['default']

    if tags:
      self.properties['Tags'] = tags

    # userdata_files takes precedence over userdata_script
    if userdata_files:
      self.properties['UserData'] = self._format_userdata(userdata_files)
    elif userdata_script:
      self.properties['UserData'] = fn_join('', userdata_script.readliens())

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


def file2cfn(fh):
  return {'Fn::Join': ['', fh.readlines()]}

def json2cfn(fh):
  s = json.load(fh)
  t = cfn.Template()
  if 'Description' in s:
    t.Description = s['Description']
  if 'Mappings' in s:
    t.Mappings = s['Mappings']
  if 'Outputs' in s:
    t.Outputs = s['Outputs']
  if 'Parameters' in s:
    t.Parameters = s['Parameters']
  if 'Resources' in s:
    t.Resources = s['Resources']
  return t

if __name__ == '__main__':
  t = json2cfn(open('scratch.json', 'r'))
  print t.dumps()
