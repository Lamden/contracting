import ast

code = open('./example_contracts/_01_currency.seneca', 'r').read()

def node_is_import(n):
	return isinstance(n, ast.Import) or isinstance(n, ast.ImportFrom)

tree = ast.parse(code)

imports = [node for node in tree.body if node_is_import(node)]
nonimports = [node for node in tree.body if not node_is_import(node)]

for i in imports:
	print(i)

print(imports)
print(nonimports)