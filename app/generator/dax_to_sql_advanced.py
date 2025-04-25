
import re

def translate_dax_to_sql(expression):
    expr = expression.strip()
    expr = re.sub(r'(?i)SUM\(', 'SUM(', expr)
    expr = re.sub(r'(?i)AVERAGE\(', 'AVG(', expr)
    expr = re.sub(r'(?i)IF\((.*?),\s*(.*?),\s*(.*?)\)', r'CASE WHEN \1 THEN \2 ELSE \3 END', expr)
    expr = re.sub(r'(?i)DIVIDE\((.*?),\s*(.*?)\)', r'COALESCE(\1 / NULLIF(\2, 0), 0)', expr)
    if 'CALCULATE' in expr.upper():
        expr = '-- REVIEW: CALCULATE not automatically translatable\n-- Original: ' + expr
    return expr
