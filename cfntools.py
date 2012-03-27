#!/usr/bin/env python

import json
from bidict import bidict
import cloudformation as cfn

def fn_join(sep, lst):
  return {'Fn:Join': [sep, lst]}

class Stack(object):

  def __init__(self, description = "", version="2010-09-09"):
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


class Resource(object):

  keymap = {'Properties': 'properties', 'Metadata': 'metadata'}

  def __init__(self, resource_type):
    self.resource_type = resource_type

  @property
  def template(self):
    T = {'Type': self.resource_type}
    for key, attrib_name in self.keymap.items():
      try:
        attrib = getattr(self, attrib_name)
      except AttributeError:
        pass
      else:
        if attrib:
          T[key] = attrib
    return T


class BaseInstance(Resource):

  def __init__(self):
    super(BaseInstance, self).__init__(resource_type='AWS::EC2::Instance')
    self.properties = {}
    self.metadata = {}


class EC2Instance(BaseInstance):

  def __init__(self, image_id, key, instance_type, userdata_files=[],
               userdata_script='', security_groups=[], tags=[]):
    super(EC2Instance, self).__init__()
    self.properties['InstanceType'] = instance_type
    self.properties['ImageId'] = image_id
    self.properties['KeyName'] = key
    self.properties['SecurityGroups'] = security_groups
    self.properties['Tags'] = tags
    if userdata_files:
      self.properties['UserData'] = self._format_userdata(userdata_files)
    if userdata_script:
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
