"""AWS CloudFormation Intrinsic Functions"""

__all__ = ['fn_join', 'fn_getatt']


def fn_join(sep, lst):
  return {'Fn:Join': [sep, lst]}

def fn_getatt(parameterised_object):
  # takes "object[parameter]"
  regex = re.compile(r'(?P<object>[^[]+)\[(?P<parameter>\w+)\]')
  g = regex.match(parameterised_object).groupdict()
  return {"Fn:GetAtt": [g['object'], g['parameter']]}
