import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression into basic tokens (words, operators, brackets).
    """
    tokens = re.findall(r'[\w\[\]\.]+|[(),=<>+\-*/]', expression)
    return [t.strip() for t in tokens if t.strip()]