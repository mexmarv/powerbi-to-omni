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

def split_on_comma(tokens):
    """Split a list of tokens on the first top-level comma"""
    depth = 0
    for i, tok in enumerate(tokens):
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth -= 1
        elif tok == "," and depth == 0:
            return tokens[:i], tokens[i+1:]
    return tokens, []

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
            full_expr, j = extract_expression(tokens, i + 1)
            left_tokens, right_tokens = split_on_comma(full_expr)
            left_sql = translate_dax_ast(" ".join(left_tokens), measures_dict)
            right_sql = translate_dax_ast(" ".join(right_tokens), measures_dict)
            sql.append(f"COALESCE(({left_sql}) / NULLIF(({right_sql}), 0), 0)")
            i = j
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
            full_expr, j = extract_expression(tokens, i + 1)
            agg_tokens, filter_tokens = split_on_comma(full_expr)
            agg_sql = translate_dax_ast(" ".join(agg_tokens), measures_dict)

            if len(filter_tokens) >= 4 and filter_tokens[0].upper() == "SAMEPERIODLASTYEAR":
                if filter_tokens[1] == "(" and filter_tokens[-1] == ")":
                    date_col = filter_tokens[2].strip("[]")
                    sql_expr = f"""
{agg_sql}
-- Filter applied using DATEADD for SAMEPERIODLASTYEAR
WHERE {date_col} IN (
    SELECT DATEADD({date_col}, -1, 'year')
)
"""
                    sql.append(sql_expr.strip())
                    i = j
                    continue
            else:
                sql.append(f"-- REVIEW: Unsupported filter in CALCULATE: {' '.join(filter_tokens)}")
                break

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