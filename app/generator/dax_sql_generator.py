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
    return expr[1:-1], i

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
            if current:
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

def translate_dax_ast(expression, measures_dict=None, vars_dict=None):
    expression = resolve_measure_refs(expression, measures_dict or {})
    tokens = tokenize_dax(expression)
    vars_dict = vars_dict or {}
    sql = []
    i = 0

    while i < len(tokens):
        tok = tokens[i].upper()

        if tok == "VAR":
            var_name = tokens[i + 1]
            if tokens[i + 2] == "=":
                var_expr, j = extract_expression(tokens, i + 3)
                vars_dict[var_name] = translate_dax_ast(" ".join(var_expr), measures_dict, vars_dict)
                i = j
                continue

        if tok == "RETURN":
            return_expr = " ".join(tokens[i + 1:])
            return translate_dax_ast(return_expr, measures_dict, vars_dict)

        if tok in vars_dict:
            sql.append(vars_dict[tok])
            i += 1
            continue

        if tok == "DIVIDE":
            full_expr, j = extract_expression(tokens, i + 1)
            args = split_on_comma(full_expr)
            if len(args) == 2:
                left_sql = translate_dax_ast(" ".join(args[0]), measures_dict, vars_dict)
                right_sql = translate_dax_ast(" ".join(args[1]), measures_dict, vars_dict)
                sql.append(f"COALESCE(({left_sql}) / NULLIF(({right_sql}), 0), 0)")
            else:
                sql.append("-- REVIEW: Invalid DIVIDE syntax")
            i = j
            continue

        if tok == "RANKX":
            full_expr, j = extract_expression(tokens, i + 1)
            args = split_on_comma(full_expr)
            if len(args) >= 2:
                rank_expr = translate_dax_ast(" ".join(args[1]), measures_dict, vars_dict)
                sql.append(f"RANK() OVER (ORDER BY {rank_expr} DESC)")
            else:
                sql.append("-- REVIEW: Invalid RANKX syntax")
            i = j
            continue

        if tok == "SWITCH":
            full_expr, j = extract_expression(tokens, i + 1)
            args = split_on_comma(full_expr)
            if args and args[0][0].upper() == "TRUE":
                branches = args[1:]
                sql_expr = "CASE "
                for k in range(0, len(branches) - 1, 2):
                    cond = translate_dax_ast(" ".join(branches[k]), measures_dict, vars_dict)
                    result = translate_dax_ast(" ".join(branches[k + 1]), measures_dict, vars_dict)
                    sql_expr += f"WHEN {cond} THEN {result} "
                if len(branches) % 2 == 1:
                    default = translate_dax_ast(" ".join(branches[-1]), measures_dict, vars_dict)
                    sql_expr += f"ELSE {default} "
                sql_expr += "END"
                sql.append(sql_expr)
                i = j
                continue

        if tok == "ISBLANK":
            inner, j = extract_expression(tokens, i + 1)
            sql.append(f"{translate_dax_ast(' '.join(inner))} IS NULL")
            i = j
            continue

        if tok == "HASONEVALUE":
            inner, j = extract_expression(tokens, i + 1)
            col = translate_dax_ast(" ".join(inner), measures_dict)
            sql.append(f"COUNT(DISTINCT {col}) = 1")
            i = j
            continue

        if tok == "SELECTEDVALUE":
            inner, j = extract_expression(tokens, i + 1)
            col = translate_dax_ast(" ".join(inner), measures_dict)
            sql.append(f"MAX({col}) -- SELECTEDVALUE simulated as MAX()")
            i = j
            continue

        if tok == "RELATED":
            inner, j = extract_expression(tokens, i + 1)
            sql.append(f"{'.'.join(inner)} -- RELATED simulated")
            i = j
            continue

        if tok == "IF":
            full_expr, j = extract_expression(tokens, i + 1)
            args = split_on_comma(full_expr)
            if len(args) == 3 and all(args):
                cond_sql = translate_dax_ast(" ".join(args[0]), measures_dict, vars_dict)
                then_sql = translate_dax_ast(" ".join(args[1]), measures_dict, vars_dict)
                else_sql = translate_dax_ast(" ".join(args[2]), measures_dict, vars_dict)
                sql.append(f"CASE WHEN {cond_sql} THEN {then_sql} ELSE {else_sql} END")
            else:
                sql.append(f"-- REVIEW: Invalid IF syntax: {full_expr}")
            i = j
            continue

        elif tok in ["+", "-", "*", "/", "=", "<", ">", "<=", ">=", "<>"]:
            sql.append(tok)
            i += 1
            continue

        elif re.match(r"\d+(\.\d+)?", tokens[i]):
            sql.append(tokens[i])
            i += 1
            continue

        elif re.match(r"\[.*?\]|[\w\\.]+", tokens[i]):
            sql.append(format_dax_column(tokens[i]))
            i += 1
            continue

        elif tok == "(":
            inner_expr, j = extract_expression(tokens, i)
            inner_sql = translate_dax_ast(" ".join(inner_expr), measures_dict, vars_dict)
            sql.append(f"({inner_sql})")
            i = j
            continue

        else:
            sql.append(f"-- Unsupported token: {tokens[i]}")
            break

    return " ".join(sql)