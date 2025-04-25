import re
from generator.dax_parser import tokenize_dax
from generator.resolve import resolve_measure_refs

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
            left = tokens[i+2].strip("[]")
            right = tokens[i+4].strip("[]")
            sql.append(f"COALESCE({left} / NULLIF({right}, 0), 0)")
            i += 6

        elif tok == "IF":
            condition = tokens[i+2:i+6]
            condition_str = " ".join(condition).replace("[", "").replace("]", "")
            then = tokens[i+6]
            _else = tokens[i+8]
            sql.append(f"CASE WHEN {condition_str} THEN {then} ELSE {_else} END")
            i += 10

        elif tok == "CALCULATE":
            try:
                agg_func = tokens[i+2].upper()           # e.g. SUM
                agg_col = tokens[i+4].strip("[]")        # e.g. Sales[amount]
                filter_func = tokens[i+7].upper()        # e.g. SAMEPERIODLASTYEAR
                filter_col = tokens[i+9].strip("[]")     # e.g. Sales[order_date]

                if filter_func == "SAMEPERIODLASTYEAR":
                    sql_expr = f"""
SUM({agg_col})
-- Filter applied using DATEADD for SAMEPERIODLASTYEAR
WHERE {filter_col} IN (
    SELECT DATEADD({filter_col}, -1, 'year')
)
"""
                    sql.append(sql_expr.strip())
                    i += 11
                else:
                    sql.append(f"-- REVIEW: Unsupported filter in CALCULATE: {filter_func}")
                    break

            except Exception as e:
                sql.append(f"-- REVIEW: Failed to parse CALCULATE: {str(e)}")
                break

        else:
            sql.append(f"-- Unsupported token: {tok}")
            break

    return " ".join(sql)