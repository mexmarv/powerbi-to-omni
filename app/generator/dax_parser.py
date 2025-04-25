import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression into a list of tokens:
    - [table[column]]
    - operators (=, <, >, etc)
    - numbers (1000, 1.25)
    - identifiers
    - parentheses and commas
    """
    pattern = r"""
        (\w+\[\w+\])              |  # table[column]
        (\[\w+\])                 |  # [column]
        (\d+(\.\d+)?)             |  # number
        ([A-Za-z_]\w*)            |  # identifier
        (<=|>=|<>|=|<|>|[-+*/(),])   # operators & punctuation
    """

    regex = re.compile(pattern, re.VERBOSE)
    tokens = []

    for match in regex.finditer(expression):
        token = match.group(0)
        if token and token.strip():
            tokens.append(token.strip())

    return tokens