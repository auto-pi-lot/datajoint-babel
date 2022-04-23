![PyPI](https://img.shields.io/pypi/v/datajoint-babel)
![PyPI - Status](https://img.shields.io/pypi/status/datajoint-babel)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/datajoint-babel)

# datajoint-babel
Generate schema code from model definitions for both Python and MATLAB (and eventually vice versa).

Say you're a lab that uses both Python and MATLAB, this lets you declare your models once and then generate
both Python and MATLAB versions of them, rather than having two potentially mutually contradictory sets of
models. Keep explicit structure and avoid implicit model recreation from the database <3.

More generally a pythonic adapter interface from an explicit data model (thanks [pydantic](https://pydantic-docs.helpmanual.io/)!) to datajoint models so other tools can 
patch in more easily!

So far just a single afternoon project, but will be the means by which autopilot interfaces directly with datajoint :)

# Example

## Source a model from a string

```python
>>> from datajoint_babel.model import Table
>>> from pprint import pprint
>>> tab = Table.from_definition(name='User', tier='Manual', definition="""
    # database users
    username : varchar(20)   # unique user name
    ---
    first_name : varchar(30)
    last_name  : varchar(30)
    role : enum('admin', 'contributor', 'viewer')
    """
)
>>> tab.dict()
{'name': 'User',
 'tier': 'Manual',
 'comment': {'comment': 'database users'},
 'keys': [{'name': 'username',
   'datatype': {'datatype': 'varchar', 'args': 20, 'unsigned': False},
   'comment': 'unique user name',
   'default': None}],
 'attributes': [{'name': 'first_name',
   'datatype': {'datatype': 'varchar', 'args': 30, 'unsigned': False},
   'comment': '',
   'default': None},
  {'name': 'last_name',
   'datatype': {'datatype': 'varchar', 'args': 30, 'unsigned': False},
   'comment': '',
   'default': None},
  {'name': 'role',
   'datatype': {'datatype': 'enum',
    'args': ["'admin'", " 'contributor'", " 'viewer'"],
    'unsigned': False},
   'comment': '',
   'default': None}]}

>>> pprint(tab.__dict__)
{'attributes': [Attribute(name='first_name', datatype=DJ_Type(datatype='varchar', args=30, unsigned=False), comment='', default=None),
                Attribute(name='last_name', datatype=DJ_Type(datatype='varchar', args=30, unsigned=False), comment='', default=None),
                Attribute(name='role', datatype=DJ_Type(datatype='enum', args=["'admin'", " 'contributor'", " 'viewer'"], unsigned=False), comment='', default=None)],
 'comment': Comment(comment='database users'),
 'keys': [Attribute(name='username', datatype=DJ_Type(datatype='varchar', args=20, unsigned=False), comment='unique user name', default=None)],
 'name': 'User',
 'tier': 'Manual'}
```

## Export to python...

```python
>>> print(tab.make(lang='python'))

@schema
class User(dj.Manual):
    definition = """
    # database users
    username : varchar(20) # unique user name
    ---
    first_name : varchar(30)
    last_name : varchar(30)
    role : enum('admin', 'contributor', 'viewer')
```

## And to MATLAB

```python
>>> print(tab.make(lang='matlab'))

%{
# # database users
# username : varchar(20) # unique user name
---
# first_name : varchar(30)
# last_name : varchar(30)
# role : enum('admin', 'contributor', 'viewer')
%}
classdef User < dj.Manual
end
```

