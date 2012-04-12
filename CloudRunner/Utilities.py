from contracts import contract  # PyContracts

class TypedDict(dict):

  # keyspec is a dict of keyname:typespec mapings --
  # typespec as defined in PyContracts
  def __init__(self, keyspec, *args, **kwargs):

    # create a contract-bound setter method for every allowed key
    for key, typespec in keyspec.items():
      setattr(self, '_set_' + key, self.__class__._create_method(key, typespec))

    super(self.__class__, self).__init__(*args, **kwargs)

  def __setitem__(self, key, value):
    try:
      getattr(self, '_set_' + key)(self, value)
    except KeyError:
      raise TypeError, "'%s' not in allowed keys" % key

  @staticmethod
  def _create_method(key, typespec):
    @contract(value=typespec)
    def m(self, value):
      super(self.__class__, self).__setitem__(key, value)
    m.__name__ = '_set_' + key
    return m
