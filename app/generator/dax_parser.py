import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression while combining table[column] references like Sales[amount].
    Handles nested functions and arithmetic expressions.
    """
    tokens = []
    i = 0
    while i < len(expression):
        c = expression[i]

        # Handle whitespace
        if c.isspace():
            i += 1
            continue

        # Handle operators and parentheses
        if c in "=<>+-*/(),":
            tokens.append(c)
            i += 1
            continue

        # Handle bracketed [column] or table[column]
        if c == '[':
            j = i
            while j < len(expression) and expression[j] != ']':
                j += 1
            if j < len(expression):  # found closing ]
                tokens.append(expression[i:j+1])
                i = j + 1
                continue
            else:
                raise ValueError("Unmatched '[' in expression")

        # Handle words or identifiers, possibly followed by [column]
        if c.isalnum() or c == '_':
            j = i
            while j < len(expression) and (expression[j].isalnum() or expression[j] in '._'):
                j += 1
            identifier = expression[i:j]
            if j < len(expression) and expression[j] == '[':
                k = j
                while k < len(expression) and expression[k] != ']':
                    k += 1
                if k < len(expression):
                    tokens.append(identifier + expression[j:k+1])
                    i = k + 1
                    continue
            tokens.append(identifier)
            i = j
            continue

        # Fallback
        i += 1

    return tokens