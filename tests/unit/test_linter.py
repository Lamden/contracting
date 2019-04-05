from unittest import TestCase
from seneca.execution.linter import Linter
import ast
from seneca.execution.whitelists import ALLOWED_AST_TYPES
from seneca.utils import CompilationException

class TestLinter(TestCase):
    def setUp(self):
        self.l = Linter()

    def test_linter(self):
        # log = get_logger("TestSenecaLinter")
        data = '''
@seneca_export
def a():
    b = 10
    return b
    '''

        print("stu code: \n{}".format(data))
        ptree = ast.parse(data)
        linter = Linter()
        status = linter.check(ptree)
        if status:
            print("Success!")
        else:
            print("Failed!")

    def test_good_ast_type(self):
        for t in ALLOWED_AST_TYPES:
            _t = t()
            self.l.ast_types(_t)

    def test_bad_ast_type(self):
        t = ast.AsyncFunctionDef()
        with self.assertRaises(CompilationException):
            self.l.ast_types(t)

    def test_not_system_variable(self):
        v = 'package'
        self.l.not_system_variable(v)

    def test_system_variable(self):
        v = '__package__'
        with self.assertRaises(CompilationException):
            self.l.not_system_variable(v)

    # def test_no_starred_imports(self):
    #     m = '*'
    #     with self.assertRaises(ImportError):
    #         self.l.valid_import_path(None, m)

    '''
    Is blocking all underscore variables really the solution to preventing access to system variables?
    '''
    def test_not_system_variable_ast(self):
        code = '''
@seneca_export
def a():
    __ruh_roh__ = 'shaggy'
        '''

        with self.assertRaises(CompilationException):
            c = ast.parse(code)
            self.l.visit(c)

    def test_not_system_variable_ast_success(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
        '''
        c = ast.parse(code)
        self.l.visit(c)

    def test_visit_async_func_def_fail(self):
        n = ast.AsyncFunctionDef()
        with self.assertRaises(CompilationException):
            self.l.visit_AsyncFunctionDef(n)

    def test_visit_async_func_def_fail_code(self):
        code = '''
@seneca_export
async def a():
    ruh_roh = 'shaggy'
'''
        with self.assertRaises(CompilationException):
            c = ast.parse(code)
            self.l.visit(c)

    def test_visit_class_fail(self):
        n = ast.ClassDef()
        with self.assertRaises(CompilationException):
            self.l.visit_ClassDef(n)

    def test_visit_class_fail_code(self):
        code = '''
class Scooby:
    pass
        '''
        with self.assertRaises(CompilationException):
            c = ast.parse(code)
            self.l.visit(c)

    def test_accessing_system_vars(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.__dir__()
'''
        with self.assertRaises(CompilationException):
            c = ast.parse(code)
            self.l.visit(c)

    def test_accessing_attribute(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.capitalize()
    '''

        c = ast.parse(code)
        self.l.visit(c)

    def test_no_nested_imports(self):
        code = '''
@seneca_export
def a():
    import something
        '''

        with self.assertRaises(CompilationException):
            c = ast.parse(code)
            self.l.visit(c)

    def test_augassign(self):
        code = '''
@seneca_export
def a():
    b = 0
    b += 1
'''
        c = ast.parse(code)
        self.l.visit(c)