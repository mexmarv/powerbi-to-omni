import re
from generator.dax_parser import tokenize_dax
from generator.resolve import resolve_measure_refs

def extract_expression(tokens, start):
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
    depth = 0
    args = []
    current = []
    for tok in tokens:
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth -= 1
        if tok == "," and depth == 0:
            args.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        args.append(current)
    return args

def format_dax_column(dax_ref):
    if "[" in dax_ref and "]" in dax_ref:
        table, column = dax_ref.split("[", 1)
        column = column.rstrip("]")
        return f"{table}.{column}"
    return dax_ref

def translate_dax_ast(expression, measures_dict=None):
    expression = resolve_measure_refs(expression, measures_dict or {})
    tokens = tokenize_dax(expression)
    sql = []
    i = 0

    while i < len(tokens):
        tok = tokens[i].upper()

        if tok == "SUM":
            inner_expr, end = extract_expression(tokens, i + 1)
            sql.append(f"SUM({' '.join(inner_expr)})")
            i = end
            continue

        elif tok == "DIVIDE":
            full_expr, j = extract_expression(tokens, i + 1)
            args = split_on_comma(full_expr)
            if len(args) == 2:
                left_sql = translate_dax_ast(" ".join(args[0]), measures_dict)
                right_sql = translate_dax_ast(" ".join(args[1]), measures_dict)
                sql.append(f"COALESCE(({left_sql}) / NULLIF(({right_sql}), 0), 0)")
            else:
                sql.append("-- REVIEW: Invalid DIVIDE syntax")
            i = j
            continue

        elif tok == "IF":
            full_expr, j = extract_expression(tokens, i + 1)
            args = split_on_comma(full_expr)
            if len(args) == 3:
                cond_sql = translate_dax_ast(" ".join(args[0]), measures_dict)
                then_sql = translate_dax_ast(" ".join(args[1]), measures_dict)
                else_sql = translate_dax_ast(" ".join(args[2]), measures_dict)
                sql.append(f"CASE WHEN {cond_sql} THEN {then_sql} ELSE {else_sql} END")
            else:
                sql.append("-- REVIEW: Invalid IF syntax")
            i = j
            continue

        elif tok == "CALCULATE":
            full_expr, j = extract_expression(tokens, i + 1)
            agg_tokens, filter_tokens = split_on_comma(full_expr)
            agg_sql = translate_dax_ast(" ".join(agg_tokens), measures_dict)

            # SAMEPERIODLASTYEAR
            if len(filter_tokens) >= 4 and filter_tokens[0].upper() == "SAMEPERIODLASTYEAR":
                dax_col = filter_tokens[2]
                sql_col = format_dax_column(dax_col)
                sql_expr = f"""
{agg_sql}
-- Filter applied using DATEADD for SAMEPERIODLASTYEAR
WHERE {sql_col} IN (
    SELECT DATEADD({sql_col}, -1, 'year')
)
"""
                sql.append(sql_expr.strip())
                i = j
                continue

            # FILTER(table, condition)
            if len(filter_tokens) >= 3 and filter_tokens[0].upper() == "FILTER":
                _, k = extract_expression(filter_tokens, 1)
                filter_args = split_on_comma(filter_tokens[2:k])
                if len(filter_args) == 2:
                    table_sql = translate_dax_ast(" ".join(filter_args[0]), measures_dict)
                    cond_sql = translate_dax_ast(" ".join(filter_args[1]), measures_dict)
                    sql_expr = f"""
{agg_sql}
-- Filter applied using FILTER
FROM {table_sql}
WHERE {cond_sql}
"""
                    sql.append(sql_expr.strip())
                    i = j
                    continue

            # ALL(...)
            if filter_tokens[0].upper() == "ALL":
                sql.append(agg_sql)  # ignore ALL, no WHERE applied
                i = j
                continue

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

        elif re.match(r"\[.*?\]|[\w\\.]+", tokens[i]):
            sql.append(format_dax_column(tokens[i]))
            i += 1
            continue

        else:
            sql.append(f"-- Unsupported token: {tokens[i]}")
            break

    return " ".join(sql)