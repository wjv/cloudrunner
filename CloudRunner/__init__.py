import json
from CFN import Stack


# Move this somewhere else?
class CFN_JSONEncoder(json.JSONEncoder):
  
  def default(self, o):
    try:
      return o.template
    except AttributeError:
      return super(Encoder, self).default(self, o)

class CFN_JSONDecoder(json.JSONDecoder):
  pass
