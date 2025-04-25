import re

def tokenize_dax(expression):
    """
    Tokenizes a DAX expression while combining table[column] references into a single token.
    Example: SUM(Sales[amount]) → ["SUM", "(", "Sales[amount]", ")"]
    """
    tokens = []
    # Basic regex to extract identifiers, brackets, and symbols
    raw = re.findall(r"(\[.*?\]|\w+|[=<>+\-*/(),])", expression)
    i = 0
    while i < len(raw):
        # Combine table[column] references
        if i + 1 < len(raw) and re.match(r"\w+", raw[i]) and raw[i+1].startswith("["):
            tokens.append(f"{raw[i]}{raw[i+1]}")  # e.g., Sales + [amount] → Sales[amount]
            i += 2
        else:
            tokens.append(raw[i])
            i += 1
    return tokens