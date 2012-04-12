import re

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

