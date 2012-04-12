from ResourceTypes import *
from IntrinsicFunctions import *
from Utilities import *


class EC2Instance(EC2_Instance):

  def __init__(self, image_id, keypair, instance_type, userdata_files=[],
               userdata_script_fh=None, cfn_init=CFN_Init(),
               security_groups=[], tags=[]):

    super(EC2Instance, self).__init__(ImageId=image_id)

    self.Properties['InstanceType'] = instance_type
    self.Properties['ImageId'] = image_id
    self.Properties['KeyPair'] = Ref(keypair)
    self.Properties['Metadata'] = cfn_init

    if security_groups:
      self.Properties['SecurityGroups'] = security_groups
    else:
      self.Properties['SecurityGroups'] = ['default']

    if tags:
      self.Properties['Tags'] = tags

    # userdata_files takes precedence over userdata_script
    if userdata_files:
      self.Properties['UserData'] = self._format_userdata(userdata_files)
    elif userdata_script_fh:
      userdata_script = InterpolatedScript(userdata_script_fh)
      self.Properties['UserData'] = \
          Fn_Base64(Fn_Join('', userdata_script.template))

    self.cfn_config = {}
    self.Metadata["AWS::CloudFormation::Init"] = {"config": self.cfn_config}

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
