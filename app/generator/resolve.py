def resolve_measure_refs(expression, measures_dict):
    """
    Replaces [measure] references with their raw DAX expression.
    """
    for ref in measures_dict:
        expression = expression.replace(f"[{ref}]", f"({measures_dict[ref]})")
    return expression