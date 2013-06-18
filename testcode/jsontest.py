#!/usr/bin/env python

from json import JSONEncoder

class Foo:

  @property
  def template(self):
    return {"foo": 123}

class Encoder(JSONEncoder):
  
  def default(self, o):
    try:
      return o.template
    except AttributeError:
      return super(Encoder, self).default(self, o)

E = Encoder()
f = Foo()
dd = {'a': 1, 'b': [2, 3, 4], "foo": f}

print E.encode(dd)

# holy cow it works
