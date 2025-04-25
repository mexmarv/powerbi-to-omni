import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression while combining table[column] references like Sales[amount].
    Handles edge cases like SUM(Sales[amount]) correctly.
    """
    pattern = r"(\w+\[\w+\])|(\[\w+\])|(\w+)|([=<>+\-*/(),])"
    matches = re.findall(pattern, expression)
    tokens = []

    for match in matches:
        token = next((part for part in match if part), "")
        if token:
            tokens.append(token)
    return tokens