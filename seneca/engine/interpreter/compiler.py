import ast
from random import choice
from string import ascii_letters, digits

from seneca.libs.logger import get_logger
from seneca.engine.interpreter.linter import Linter


# raghu todo parser functionality:
#   1. checker -> checks for right usage and pythonic code, and verifies it follows our rules of restricted usage. at least one exported function, etc
#      error -> record error and return.  Here we want to record all the errors in a contract for the maximum benefit of the user.
#      can be provided as part of a user tool set for users to develop and test also.
#   2. code transformer -> transforms the code: a) prefixing, etc, b) adds decorator and cleanup functionality
#   3. compiled codeobj, along with mod code str and other annotated datastructures for book keeping    
# raghu todo
#  1. Replace this with context to provide runtime context.
#  2. Runtime context is setup at the point of txn execution.
#     then runtime context is only runtime context: sender and stamps supplied, etc
#  3. CodeModifier will add a class with contract name
#  4. it will hide all global variables with contract_name prefix
#  5. and add a function "_seneca_set_context" -> that will take backup of global variables and set them to None
#  6. and add a function "_seneca_reset_context" -> to restore global variables to backups
#  7. then Export() or Seed() functions can wrap them around function
#  8. replacing global variables - what if one variable is a subset of another one ? we need to sort them by the length and replace longest to shortest ?
#  9. should we change internal_method names also with the prefix __seneca__
    
class SenecaCompiler(ast.NodeTransformer):

    def __init__(self, module_name, code_str, is_fixed_prefix = False):
        self.module_name = module_name
        self.code_str = code_str
        self.is_fixed_prefix = is_fixed_prefix
        self.log = get_logger('Seneca.Parser')
        self._construct_method = None       # add check to ensure only one construct function
        self._exported_methods = []
        self._internal_methods = []
        self._global_variables = []
        self._local_variables  = []   # raghu todo need to handle this for the cases where local variables use same name
                                      # should we reject nonlocal declarations (as part of linter though)?
        self._mod_var_names = []
        self._strings = []
        self._ast_tree = None
        self._add_prefix = True
        # self._is_seneca_processed = is_modified


    def lint(self):
        if not self._ast_tree:
            return False
        linter = Linter()
        return linter.check(self._ast_tree)

    def compile(self):
        # Parse tree
        assert not self._ast_tree, "Not expected to reuse this object to compile multiple codes"
        self._ast_tree = ast.parse(self.code_str)

        # should provide a list of error conditions?
        if not self.lint():
            return False

        # collect data
        self.visit(self._ast_tree)
        # collect all strings
        for node in ast.walk(self._ast_tree):
            if isinstance(node, ast.Str) and node.s not in self._strings:
                self._strings.append(node.s)
        # print(self._global_variables)
        # print(self._strings)
        # print(self._exported_methods)
        # print(self._internal_methods)
        # print(self.code_str)
        # transform the code
        self._mod_code_str = self.code_transform()
        # print(self._mod_code_str)
        return self._mod_code_str
        

    def visit_FunctionDef(self, node):
        if node.decorator_list:
            for d in node.decorator_list:
                if d.id == 'seneca_export':
                    self._exported_methods.append(node.name)
                elif d.id == 'seneca_construct':
                    self._construct_method = node.name
        else:
            self._internal_methods.append(node.name)
        return node

    def visit_Assign(self, node):
        for t in node.targets:
            self._global_variables.append(t.id)
        return node

    def visit_AugAssign(self, node):
        self._global_variables.append(node.target.id)
        return  node

    def visit_AnnAssign(self, node):
        self._global_variables.append(node.target.id)
        return  node

    def visit_Global(self, node):
        for n in node.names:
            self._global_variables.append(n)
        return  node

    def get_unique_substr(self, code_str, prefix):
        while prefix in code_str:
            prefix = prefix + 'q'
        return prefix

    # this is appended only for txn execution (not when contract is published)
    # and will not appear in output so as not to create issues in consensus
    def get_unique_random_str(self, code_str, length=3):
        if self.is_fixed_prefix:
            prefix = '_zxq'
            while prefix in code_str:
                prefix = prefix + 'q'
        else:
            rstr = ''.join(choice(ascii_letters + digits) for i in range(length))
            prefix = '_' + rstr
            while prefix in code_str:
                prefix = prefix + choice(ascii_letters + digits)
        return prefix + '_'

    def add_reset_method(self, code_str):
        if not self._mod_var_names:
            return code_str
        func_name = '_seneca_reset_context'
        code_str += "\ndef " + func_name + "():\n"
        for vname in self._mod_var_names:
            code_str += "    " + vname + " = None\n"
        return code_str

    def add_decorator(self, code_str, func_name):
        code_str += "\ndef " + func_name + "(con_func):\n"
        code_str += "    def _" + func_name + "_inner():\n"
        code_str += "        res = con_func()\n"
        code_str += "        _seneca_reset_context()\n"
        code_str += "        return res\n"
        code_str += "    return _" + func_name + "_inner\n"
        return code_str

    def add_prefixes(self, code_str):
        if not self._add_prefix:
            return code_str
        str_us_map = {}
        self._strings.sort(key=len, reverse=True)
        for sval in self._strings:
            sval1 = "'" + sval + "'"
            sval2 = '"' + sval + '"'
            rval = self.get_unique_random_str(code_str, 5)
            code_str = code_str.replace(sval1, rval)
            code_str = code_str.replace(sval2, rval)
            str_us_map[rval] = sval1

        fun_us_map = {}
        for fname in self._exported_methods:
            fname1 = ' ' + fname
            rname = self.get_unique_random_str(code_str, 5)
            code_str = code_str.replace(fname1, rname)
            str_us_map[rname] = fname1

        for fname in self._internal_methods:
            fname1 = ' ' + fname
            rname = self.get_unique_random_str(code_str, 5)
            code_str = code_str.replace(fname1, rname)
            str_us_map[rname] = fname1

        if self._construct_method:
            fname1 = ' ' + self._construct_method
            rname = self.get_unique_random_str(code_str, 5)
            code_str = code_str.replace(fname1, rname)
            str_us_map[rname] = fname1
        
        var_us_map = {}
        # sort variables from longest length to shortest
        self._global_variables.sort(key=len, reverse=True)
        for vname in self._global_variables:
            rname = self.get_unique_random_str(code_str, 5)
            code_str = code_str.replace(vname, rname)
            var_us_map[vname] = rname

        # sort variables from shortest to longest
        # self._global_variables.sort(key=len)
        for vname in self._global_variables:
            rname = var_us_map[vname]
            # fname = '_zxq_' + vname
            fname = self.get_unique_random_str(code_str) + vname
            self._mod_var_names.append(fname)
            code_str = code_str.replace(rname, fname)

        for sval, rval in str_us_map.items():
            code_str = code_str.replace(sval, rval)

        return code_str
            

    def code_transform(self):
        code_str = self.add_prefixes(self.code_str)
        code_str = self.add_reset_method(code_str)
        code_str = self.add_decorator(code_str, "seneca_export")
        if self._construct_method:
            code_str = self.add_decorator(code_str, "seneca_construct")
        return code_str


