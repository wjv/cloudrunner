import json

# Move this somewhere else?
class CFN_JSONEncoder(json.JSONEncoder):
  
  def default(self, o):
    try:
      return o.template
    except AttributeError:
      return super(self.__class__, self).default(self, o)

class CFN_JSONDecoder(json.JSONDecoder):
  pass
