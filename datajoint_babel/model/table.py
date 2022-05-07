from typing import Optional, Union, List, Literal

from pydantic import BaseModel

from datajoint_babel.constants import TIERS
from datajoint_babel.model.attribute import Comment, Attribute, Dependency


class Table(BaseModel):
    """
    Abstract representation of the components of a Datajoint Table
    """
    name: str
    # schema_name: Optional[str] = None
    tier: TIERS = 'Manual'
    comment: Optional[Comment] = None
    keys: List[Union[Attribute, Dependency]]
    attributes: Optional[List[Union[Attribute, Dependency]]] = None

    @classmethod
    def from_definition(cls, name:str, definition:str, tier:Optional[TIERS]=None) -> 'Table':

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

            if '->' in line:
                attr = Dependency.from_string(line)
            else:
                attr = Attribute.from_string(line)

            if passed_keys:
                attrs.append(attr)
            else:
                keys.append(attr)

        if tier is None:
            tier = 'MANUAL'

        return cls(name=name, tier=tier, comment=comment, keys=keys, attributes=attrs)


    def make(self, lang:Literal['python', 'matlab'] = 'python') -> str:
        if lang == 'python':
            return self._make_python()
        elif lang.lower() == 'matlab':
            return self._make_matlab()

    def _make_python(self) -> str:
        # --------------------------------------------------
        # frontmatter
        # --------------------------------------------------

        out_str = '@schema\n'
        out_str += f'class {self.name}(dj.{self.tier}):\n'
        out_str += '    definition = """\n'

        if self.comment:
            out_str += f'    {self.comment.make()}\n'

        # --------------------------------------------------
        # keys
        # --------------------------------------------------
        keys = self.keys
        if not isinstance(keys, list):
            keys = list(keys)

        for key in keys:
            out_str += f'    {key.make()}\n'

        out_str += '    ---\n'

        # --------------------------------------------------
        # attrs
        # --------------------------------------------------
        attrs = self.attributes
        if not isinstance(attrs, list):
            attrs = list(attrs)

        for attr in attrs:
            out_str += f'    {attr.make()}\n'

        out_str += '    """'

        return out_str

    def _make_matlab(self) -> str:
        out_str = "%{\n"

        if self.comment:
            out_str += f"# {self.comment.make()}\n"

        # --------------------------------------------------
        # keys
        # --------------------------------------------------
        keys = self.keys
        if not isinstance(keys, list):
            keys = list(keys)

        for key in keys:
            out_str += f"# {key.make()}\n"

        out_str += "---\n"

        # --------------------------------------------------
        # attrs
        # --------------------------------------------------
        attrs = self.attributes
        if not isinstance(attrs, list):
            attrs = list(attrs)

        for attr in attrs:
            out_str += f"# {attr.make()}\n"

        # --------------------------------------------------
        # classdef
        # --------------------------------------------------
        out_str += '%}\n\n'
        out_str += f'classdef {self.name} < dj.{self.tier}\nend'
        return out_str