import re
from generator.dax_parser import tokenize_dax
from generator.resolve import resolve_measure_refs

def extract_expression(tokens, start):
    """Extract a full expression, respecting nested parentheses."""
    depth = 0
    expr = []
    for i in range(start, len(tokens)):
        tok = tokens[i]
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth -= 1
        expr.append(tok)
        if depth == 0 and i > start:
            return expr, i
    return expr, len(tokens)

def translate_dax_ast(expression, measures_dict=None):
    expression = resolve_measure_refs(expression, measures_dict or {})
    tokens = tokenize_dax(expression)
    sql = []
    i = 0

    while i < len(tokens):
        tok = tokens[i].upper()

        if tok == "SUM":
            col = tokens[i+2].strip("[]")
            sql.append(f"SUM({col})")
            i += 4

        elif tok == "DIVIDE":
            left_expr, j = extract_expression(tokens, i+2)
            right_expr, k = extract_expression(tokens, j+2)
            left_sql = translate_dax_ast(" ".join(left_expr), measures_dict)
            right_sql = translate_dax_ast(" ".join(right_expr), measures_dict)
            sql.append(f"COALESCE(({left_sql}) / NULLIF(({right_sql}), 0), 0)")
            i = k + 1

        elif tok == "IF":
            cond_expr, j = extract_expression(tokens, i+2)
            then_expr, k = extract_expression(tokens, j+1)
            else_expr, l = extract_expression(tokens, k+1)
            sql.append(
                f"CASE WHEN {' '.join(cond_expr)} THEN {' '.join(then_expr)} ELSE {' '.join(else_expr)} END"
            )
            i = l + 1

        elif tok == "CALCULATE":
            try:
                agg_expr, j = extract_expression(tokens, i+2)
                agg_sql = translate_dax_ast(" ".join(agg_expr), measures_dict)

                filter_func = tokens[j+2].upper()
                filter_col = tokens[j+4].strip("[]")

                if filter_func == "SAMEPERIODLASTYEAR":
                    sql_expr = f"""
{agg_sql}
-- Filter applied using DATEADD for SAMEPERIODLASTYEAR
WHERE {filter_col} IN (
    SELECT DATEADD({filter_col}, -1, 'year')
)
"""
                    sql.append(sql_expr.strip())
                    i = j + 6
                else:
                    sql.append(f"-- REVIEW: Unsupported filter in CALCULATE: {filter_func}")
                    break
            except Exception as e:
                sql.append(f"-- REVIEW: Failed to parse CALCULATE: {str(e)}")
                break

        elif tok in ["+", "-", "*", "/"]:
            sql.append(tok)
            i += 1

        elif re.match(r"\[.*?\]|[\w\.]+", tok):
            sql.append(tok)
            i += 1

        else:
            sql.append(f"-- Unsupported token: {tok}")
            break

    return " ".join(sql)