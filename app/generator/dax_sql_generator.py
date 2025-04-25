import re
from generator.dax_parser import tokenize_dax
from generator.resolve import resolve_measure_refs

def extract_expression(tokens, start):
    """Extract a full expression inside nested parentheses"""
    depth = 0
    expr = []
    i = start
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth -= 1
        expr.append(tok)
        i += 1
        if depth == 0:
            break
    return expr[1:-1], i  # remove outer ( and )

def translate_dax_ast(expression, measures_dict=None):
    expression = resolve_measure_refs(expression, measures_dict or {})
    tokens = tokenize_dax(expression)
    sql = []
    i = 0

    while i < len(tokens):
        tok = tokens[i].upper()

        if tok == "SUM":
            if i + 1 < len(tokens) and tokens[i + 1] == "(":
                inner_expr, end = extract_expression(tokens, i + 1)
                sql.append(f"SUM({' '.join(inner_expr)})")
                i = end
                continue

        elif tok == "DIVIDE":
            left_expr, j = extract_expression(tokens, i + 1)
            right_expr, k = extract_expression(tokens, j)
            left_sql = translate_dax_ast(" ".join(left_expr), measures_dict)
            right_sql = translate_dax_ast(" ".join(right_expr), measures_dict)
            sql.append(f"COALESCE(({left_sql}) / NULLIF(({right_sql}), 0), 0)")
            i = k
            continue

        elif tok == "IF":
            cond_expr, j = extract_expression(tokens, i + 1)
            then_expr, k = extract_expression(tokens, j)
            else_expr, l = extract_expression(tokens, k)
            sql.append(
                f"CASE WHEN {' '.join(cond_expr)} THEN {' '.join(then_expr)} ELSE {' '.join(else_expr)} END"
            )
            i = l
            continue

        elif tok == "CALCULATE":
            agg_expr, j = extract_expression(tokens, i + 1)
            agg_sql = translate_dax_ast(" ".join(agg_expr), measures_dict)

            filter_func = tokens[j].upper() if j < len(tokens) else ""
            filter_col = tokens[j + 2].strip("[]") if j + 2 < len(tokens) else "UNKNOWN"

            if filter_func == "SAMEPERIODLASTYEAR":
                sql_expr = f"""
{agg_sql}
-- Filter applied using DATEADD for SAMEPERIODLASTYEAR
WHERE {filter_col} IN (
    SELECT DATEADD({filter_col}, -1, 'year')
)
"""
                sql.append(sql_expr.strip())
                i = j + 4
            else:
                sql.append(f"-- REVIEW: Unsupported filter in CALCULATE: {filter_func}")
                break
            continue

        elif tok == "(":
            inner_expr, j = extract_expression(tokens, i)
            inner_sql = translate_dax_ast(" ".join(inner_expr), measures_dict)
            sql.append(f"({inner_sql})")
            i = j
            continue

        elif tok in ["+", "-", "*", "/"]:
            sql.append(tok)
            i += 1
            continue

        elif re.match(r"\[.*?\]|[\w\.]+", tokens[i]):
            sql.append(tokens[i])
            i += 1
            continue

        else:
            sql.append(f"-- Unsupported token: {tokens[i]}")
            break

    return " ".join(sql)