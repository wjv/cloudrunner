import types

class RestrictedDictException(BaseException):
  pass

class rdict(dict):
  """
  A dictionary that may be restricted i.t.o. allowed key names and/or
  allowed value types.

  """
  def __init__(self, allowed_keys=[], allowed_value_types=[], *args, **kwargs):
    if allowed_keys:
      self.allowed_keys = allowed_keys
    if allowed_value_types:
      try:
        self.allowed_value_types = tuple(allowed_value_types)
      except TypeError:
        self.allowed_value_types = (allowed_value_types,)
    print args, kwargs
    super(rdict, self).__init__(*args, **kwargs)

  def __setitem__(self, key, value):
    if hasattr(self, 'allowed_keys'):
      if key not in self.allowed_keys:
        raise RestrictedDictException, "'%s' not in allowed keys" % key
    if hasattr(self, 'allowed_value_types'):
      if not isinstance(value, self.allowed_value_types):
        raise RestrictedDictException, \
          "'%s' not in allowed value types: %s" % (key, self.allowed_value_types)
    super(rdict, self).__setitem__(key, value)
