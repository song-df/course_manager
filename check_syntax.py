import ast
fp = r"D:\workspace\course_resource\server.py"
with open(fp, encoding='utf-8') as f:
    code = f.read()
try:
    ast.parse(code)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
