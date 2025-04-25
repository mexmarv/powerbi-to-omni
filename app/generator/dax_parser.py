import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression, preserving brackets and combining identifiers like Sales[amount].
    Output: ['SUM', '(', 'Sales[amount]', ')']
    """
    tokens = []
    i = 0
    while i < len(expression):
        char = expression[i]

        # Skip whitespace
        if char.isspace():
            i += 1
            continue

        # Operators and punctuation
        if char in "=<>+-*/(),":
            tokens.append(char)
            i += 1
            continue

        # Handle identifiers or functions
        if char.isalpha() or char == '_':
            start = i
            while i < len(expression) and (expression[i].isalnum() or expression[i] in '._'):
                i += 1
            name = expression[start:i]

            # If next is [, it's a table[column] combo
            if i < len(expression) and expression[i] == '[':
                bracket_start = i
                i += 1
                while i < len(expression) and expression[i] != ']':
                    i += 1
                if i < len(expression):
                    i += 1  # include closing ]
                    full = name + expression[bracket_start:i]
                    tokens.append(full)
                    continue
                else:
                    raise ValueError(f"Unclosed [ in expression after {name}")
            else:
                tokens.append(name)
                continue

        # Handle standalone [column]
        if char == '[':
            start = i
            i += 1
            while i < len(expression) and expression[i] != ']':
                i += 1
            if i < len(expression):
                i += 1
                tokens.append(expression[start:i])
                continue
            else:
                raise ValueError("Unclosed [ in expression")

        # If nothing matched, skip (or raise)
        i += 1

    return tokens