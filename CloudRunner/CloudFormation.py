import ResourceTypes
import ResourcePropertyTypes
import IntrinsicFunctions
import PseudoParameters

__all__ = ["Parameter", "Mapping", "Stack",
           "ResourceTypes", "ResourcePropertyTypes",
           "IntrinsicFunctions", "PseudoParameters"]

from bidict import bidict


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

  def __init__(self, valuenames, mapping={}):
    self.template = mapping

  def put(self, key, valuename, value):
    self.template[key][valuename] = value

  def get(self, key, valuename):
    return self.template[key][valuename]


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
    #assert isinstance(r, Resource)
    self.namespace[name] = r
    self.resources.append(r)

  def dereference(self, obj):
    """Return (obj.name, obj.template) fully resolved in Stack's namespace."""
    return self.namespace.inv[obj], obj

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
