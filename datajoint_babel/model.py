"""
Classes to represent the abstract structure of datajoint schema definitions
"""

import sys
import typing
import re
from abc import abstractmethod
from typing import Optional, Union, Tuple, List, Dict, Literal, ClassVar
from pydantic import BaseModel, Field as PyField, PrivateAttr
import parse
from enum import Enum

from datajoint.declare import TYPE_PATTERN, SPECIAL_TYPES, NATIVE_TYPES, EXTERNAL_TYPES, SERIALIZED_TYPES
from datajoint.declare import match_type, attribute_parser, foreign_key_parser, attribute_parser, index_parser
from datajoint.user_tables import Manual, Lookup, Imported, Computed, Part, UserTable


class TIERS(Enum):
    Manual = Manual
    Lookup = Lookup
    Imported = Imported
    Computed = Computed
    Part = Part

DATATYPES = Literal[
    "tinyint",
    "smallint",
    "mediumint",
    "int",
    "enum",
    "date",
    "time",
    "datetime",
    "timestamp",
    "char",
    "varchar",
    "float",
    "double",
    "decimal",
    "blob",
    "tinyblob",
    "mediumblob",
    "longblob",
    "attach",
    "filepath"
]


# TIER_MAP = {
#     'Manual': Manual,
#     'Lookup': Lookup,
#     'Imported': Imported,
#     'Computed': Computed,
#     'Part': Part
# }

# TIERS = Literal['Manual', 'Lookup', 'Imported', 'Computed']

class ParseError(Exception):
    """Exception raise when a row can't be parsed from text"""

    @classmethod
    def format_raise(cls, format:str, input:str):
        """
        Raises with an informative error about the format string
        """
        error_str = f"Could not parse table row.\nExpected Format: {format}\nGot String: {input}"
        raise cls(error_str)

class TableRow(BaseModel):
    """
    Abstract base class for rows in a datajoint table
    """

    @abstractmethod
    def make(self) -> str:
        """
        Given the properties of this row, generate the string form
        """

    @classmethod
    @abstractmethod
    def from_string(cls, input:str) -> 'TableRow':
        """
        Make an instance of this type of row from a string

        Raises:
            :class:`.ParseError` if the string can't be parsed
        """


class Comment(TableRow):
    comment: str
    _format: ClassVar[str]= "# {comment}"

    def make(self) -> str:
        return ' '.join(['#', self.comment])

    @classmethod
    def from_string(cls, input:str) -> 'Comment':
        comment = parse.parse(cls._format, input)
        if comment is None:
            ParseError.format_raise(cls._format, input)
        return cls(**comment.named)

class DJ_Type(BaseModel):
    """
    Representation of a datajoint type
    """
    datatype: DATATYPES
    args: Optional[Union[int, List[int], List[str]]] = None
    unsigned: bool = False
    _parameterized_format: ClassVar[str] = "{datatype}({args})"

    def make(self) -> str:
        typestr = self.datatype
        if self.args:
            if self.datatype == 'filepath':
                typestr += f'@{self.args}'
            elif isinstance(self.args, list):
                typestr += f'({",".join(self.args)})'
            else:
                typestr += f'({self.args})'

        if self.unsigned:
            typestr += ' unsigned'

        return typestr

    @classmethod
    def from_string(cls, input:str) -> 'DJ_Type':
        # from https://github.com/datajoint/datajoint-python/blob/56ced5dabe84687ce33f14c02889fe546c9bbc80/datajoint/declare.py#L344
        unsigned = False
        if 'unsigned' in input:
            unsigned = True
            input = input.rstrip(' unsigned')

        if '@' in input:
            # filepath
            datatype, args = '@'.split(input)
            return cls(datatype=datatype, args=args)

        input = input.strip()

        parameterized = parse.parse(cls._parameterized_format, input)
        if parameterized is None:
            args = None
            datatype = input
        else:
            args = parameterized.named['args']
            datatype = parameterized.named['datatype']
            if ',' in args:
                args = args.split(',')


        return cls(datatype=datatype, args=args, unsigned=unsigned)


class Attribute(TableRow):
    """
    A field that specifies a data type, and optionally a default and comment

    Valid formats:

        *
        *
        *
        *

    """
    name: str
    datatype: DJ_Type
    comment: Optional[str] = None
    default: Optional[typing.Any] = None

    def make(self) -> str:
        if self.comment and self.default:
            return f"{self.name} = {self.default} : {self.datatype.make()} # {self.comment}"
        elif self.comment:
            return f"{self.name} : {self.datatype.make()} # {self.comment}"
        elif self.default:
            return f"{self.name} = {self.default} : {self.datatype.make()}"
        else:
            return f"{self.name} : {self.datatype.make()}"


    @classmethod
    def from_string(cls, input:str) -> 'Attribute':
        if re.match(r"^(unique\s+)?index[^:]*$", input, re.I):
            raise NotImplementedError()

        # following https://github.com/datajoint/datajoint-python/blob/56ced5dabe84687ce33f14c02889fe546c9bbc80/datajoint/declare.py#L566
        pieces = attribute_parser.parseString(input + '#')
        pieces['comment'] = pieces['comment'].rstrip('#').strip()
        if 'default' not in pieces:
            pieces['default'] = None

        return cls(
            name=pieces['name'],
            datatype=DJ_Type.from_string(pieces['type']),
            comment=pieces['comment'],
            default=pieces['default']
        )


class Table(BaseModel):
    """
    Abstract representation of the components of a Datajoint Table
    """
    name: str
    # schema_name: Optional[str] = None
    tier: TIERS = 'Manual'
    comment: Optional[Comment] = None
    keys: Union[Attribute, List[Attribute]]
    attributes: Union[Attribute, List[Attribute]]

    @classmethod
    def from_definition(cls,name:str, definition:str,  tier:Optional[TIERS]=None) -> 'Table':
        if isinstance(tier, str):
            tier = TIERS.__members__[tier]

        lines = definition.split('\n')

        passed_keys = False
        comment = None
        keys = []
        attrs = []
        for line in lines:
            line = line.strip()
            if len(line) == 0:
                continue

            if line.startswith('#'):
                comment = Comment.from_string(line)
                continue

            if '---' in line:
                passed_keys = True
                continue

            if passed_keys:
                attrs.append(Attribute.from_string(line))
            else:
                keys.append(Attribute.from_string(line))

        return cls(name=name, tier=tier, comment=comment, keys=keys, attributes=attrs)


    def make(self, lang:Literal['python', 'matlab'] = 'python') -> str:
        if lang == 'python':
            return self._make_python()
        elif lang.lower() == 'matlab':
            return self._make_matlab()

    def _make_python(self) -> str:
        out_str = '@schema\n'
        out_str += f'class {self.name}(dj.{self.tier.name}):\n'
        out_str += '    definition = """\n'

        if self.comment:
            out_str += f'    {self.comment.make()}\n'

        keys = self.keys
        if not isinstance(keys, list):
            keys = list(keys)

        for key in keys:
            out_str += f'    {key.make()}\n'

        out_str += '    ---\n'

        attrs = self.attributes
        if not isinstance(attrs, list):
            attrs = list(attrs)

        for attr in attrs:
            out_str += f'    {attr.make()}\n'

        return out_str

    def _make_matlab(self) -> str:
        raise NotImplementedError()


definition = """
# database users
username : varchar(20)   # unique user name
---
first_name : varchar(30)
last_name  : varchar(30)
role : enum('admin', 'contributor', 'viewer')
"""