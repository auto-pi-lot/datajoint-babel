import re
import typing
from abc import abstractmethod
from typing import ClassVar, Optional, Union, List

import parse
from datajoint.declare import attribute_parser
from pydantic import BaseModel

from datajoint_babel.constants import DATATYPES
from datajoint_babel.exceptions import ParseError, ResolutionError
from datajoint_babel.spawn import spawn_all_schema


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
                _args = [str(a) for a in self.args]
                typestr += f'({",".join(_args)})'
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

        * ``name : datatype``
        * ``name : datatype # comment ``
        * ``name = default : datatype``
        * ``name = default : datatype # comment``

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


class Dependency(TableRow):
    dependency: str
    _format: ClassVar[str] = "-> {dependency}"

    def make(self) -> str:
        return f"-> {self.dependency}"

    @classmethod
    def from_string(cls, input:str) -> 'Dependency':
        dependency = parse.parse(cls._format, input)
        if dependency is None:
            ParseError.format_raise(cls._format, input)
        return cls(**dependency.named)

    def resolve_keys(self) -> list[str]:
        """
        Spawn all schema and try to find the primary keys that this dependency refers to

        Returns:
            List of primary keys
        """
        schema = spawn_all_schema()
        ours = [sch for sch in schema if sch.__name__ == self.dependency]
        if len(ours) == 0:
            raise ResolutionError(f"Could not resolve dependent schema {self.dependency}")
        return ours[0].primary_key



