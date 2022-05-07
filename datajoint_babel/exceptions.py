class ParseError(Exception):
    """Exception raise when a row can't be parsed from text"""

    @classmethod
    def format_raise(cls, format:str, input:str):
        """
        Raises with an informative error about the format string
        """
        error_str = f"Could not parse table row.\nExpected Format: {format}\nGot String: {input}"
        raise cls(error_str)


class ResolutionError(Exception):
    """Could not resolve a dependency!"""