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
