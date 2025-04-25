import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression while keeping [bracketed] identifiers and respecting punctuation.
    """
    pattern = r"(\[.*?\]|[A-Za-z_][\w\.]*)|([=<>+\-*/(),])"
    tokens = []
    for match in re.finditer(pattern, expression):
        token = match.group().strip()
        if token:
            tokens.append(token)
    return tokens