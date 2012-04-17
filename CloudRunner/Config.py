import re

from ResourceTypes import ResourceType

__all__ = ["CloudFormation_Init", "Config", "InterpolatedScript"]


class CloudFormation_Init(ResourceType):

  """AWS::CloudFormation::Init"""

  # Is officialy a Resource Type, but doesn't quite act like one --
  # no Type attribute, no Properties, &c.
  # NOTE that generally we either contain one configset and a bunch of configs,
  # or a single config named 'config'.

  def __init__(self, template={}):
    self.Type = "AWS::CloudFormation::Init"""
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


class Config(object):

  from string import ascii_lowercase as a_l
  cmd_indices = [c + d for c in a_l for d in a_l]       # 'aa', 'ab', ..., 'zz'

  template_attributes = ['commands', 'files', 'groups', 'packages', 'services',
                         'sources', 'users']
  pkg_types = ['yum', 'python', 'ruby']         # XXX expand
  srv_types = ['sysvinit']

  def __init__(self, template={}):
    if template:
      self.__dict__.update(template)              # XXX is this kosher?
    else:
      for attrib in self.template_attributes:
        setattr(self, attrib, {})

  def add_package(self, pkg_type, name, versions=[]):
    if not isinstance(versions, list):
      versions = [versions]
    type_dict = self.packages.setdefault(pkg_type, {})
    type_dict[name] = versions

  def add_service(self, srv_name, srv_type='sysvinit',
                  enabled=None, ensureRunning=None,
                  files=[], sources=[], packages={}, commands=[]):
    type_dict = self.services.setdefault(srv_type, {})
    srv_dict = type_dict.setdefault(srv_name, {})
    for param in "enabled", "ensureRunning":
      value = vars()[param]
      if value is not None:
        srv_dict[param] = value and "true" or "false"
      for param in "files", "sources", "packages", "commands":
        value = vars()[param]
        if value:
          srv_dict[param] = value


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
    if not self.commands:
      prefix = 'aa'
    else:
      last_prefix = sorted(self.commands.keys())[-1].split('_')[0]
      prefix = self._next_cmdprefix(last_prefix)
    self.commands['_'.join([prefix, name])] = command

  @property
  def template(self):
    return dict((k, v) for k, v in self.__dict__.items()
                if v and k in self.template_attributes)

