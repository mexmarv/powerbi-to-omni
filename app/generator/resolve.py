def resolve_measure_refs(expression, measures_dict):
    for ref in measures_dict:
        expression = expression.replace(f"[{ref}]", f"({measures_dict[ref]})")
    return expression