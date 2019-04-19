from unittest import TestCase
from seneca.execution.linter import Linter
import ast
from seneca.execution.whitelists import ALLOWED_AST_TYPES


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
            self.assertListEqual([], self.l._violations)

    def test_bad_ast_type(self):
        err = 'Error : Illegal AST type: AsyncFunctionDef'
        t = ast.AsyncFunctionDef()
        self.l.ast_types(t)
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_not_system_variable(self):
        v = 'package'
        self.l.not_system_variable(v)
        self.assertListEqual([], self.l._violations)

    def test_system_variable(self):
        v = '__package__'
        err = "Error : Incorrect use of <_> access denied for var : __package__"
        self.l.not_system_variable(v)
        self.assertMultiLineEqual(err, self.l._violations[0])

    '''
    Is blocking all underscore variables really the solution to preventing access to system variables?
    '''
    def test_not_system_variable_ast(self):
        code = '''
@seneca_export
def a():
    __ruh_roh__ = 'shaggy'
        '''
        err = 'Error : Incorrect use of <_> access denied for var : __ruh_roh__'

        c = ast.parse(code)
        self.l.visit(c)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_not_system_variable_ast_success(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
        '''
        c = ast.parse(code)
        self.l.visit(c)
        self.assertListEqual([], self.l._violations)

    def test_visit_async_func_def_fail(self):
        err = 'Error : Illegal AST type: AsyncFunctionDef'
        n = ast.AsyncFunctionDef()

        self.l.visit_AsyncFunctionDef(n)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_visit_async_func_def_fail_code(self):
        code = '''
@seneca_export
async def a():
    ruh_roh = 'shaggy'
'''
        err = 'Error : Illegal AST type: AsyncFunctionDef'

        c = ast.parse(code)
        self.l.visit(c)
        self.assertMultiLineEqual(err, self.l._violations[0])


    def test_visit_class_fail(self):
        err = 'Error : Illegal AST type: ClassDef'
        n = ast.ClassDef()
        self.l.visit_ClassDef(n)
        self.l.dump_violations()

        self.assertMultiLineEqual(err, self.l._violations[0])


    def test_visit_class_fail_code(self):
        code = '''
class Scooby:
    pass
        '''
        err = 'Error : Illegal AST type: ClassDef'

        c = ast.parse(code)
        self.l.visit(c)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])


    def test_accessing_system_vars(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.__dir__()
'''
        err = 'Error : Incorrect use of <_> access denied for var : __dir__'
        c = ast.parse(code)
        self.l.visit(c)
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_accessing_attribute(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.capitalize()
    '''

        c = ast.parse(code)
        self.l.visit(c)
        self.assertListEqual([], self.l._violations)

#TODO failed test case

    def test_no_nested_imports(self):
        code = '''
@seneca_export
def a():
    import something
        '''

        c = ast.parse(code)
        self.l.visit(c)
        self.l.dump_violations()


    def test_no_nested_imports_works(self):
        code = '''
@seneca_export
def a():
    ruh_roh = 'shaggy'
    ruh_roh.capitalize()
            '''

        c = ast.parse(code)
        self.l.no_nested_imports(c)
        self.l.dump_violations()
        self.assertListEqual([], self.l._violations)



    def test_augassign(self):
        code = '''
@seneca_export
def a():
    b = 0
    b += 1
'''
        c = ast.parse(code)
        self.l.visit(c)
        self.assertListEqual([], self.l._violations)

    def test_import_works(self):
        self.l.driver.set_contract('something', 'a = 10')
        code = '''
import something
@seneca_export
def a():
    b = 0
    b += 1
        '''

        c = ast.parse(code)
        self.l.visit(c)
        self.l.driver.flush()
        self.assertListEqual([], self.l._violations)


    def test_no_import_from(self):
        code = '''
from something import a
@seneca_export
def a():
    b = 0
    b += 1
'''
        err = 'ImportFrom ast nodes not yet supported.'

        c = ast.parse(code)
        self.l.visit(c)
        self.l.dump_violations()
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_import_non_existent_contract(self):
        code = '''
import something
@seneca_export
def a():
    b = 0
    b += 1
'''
        err = 'Contract named "something" does not exist in state.'

        c = ast.parse(code)
        self.l.visit(c)
        self.assertMultiLineEqual(err, self.l._violations[0])

    def test_final_checks_set_properly(self):
        code = '''
def a():
    b = 0
    b += 1
        '''

        c = ast.parse(code)
        self.l.visit(c)
        self.l._final_checks()

        self.assertFalse(self.l._is_one_export)

    def test_collect_function_defs(self):
        code = '''
@seneca_export
def a():
    return 42

@seneca_export
def b():
    return 1000000

@seneca_export
def x():
    return 64

@seneca_export
def y():
    return 24
'''
        c = ast.parse(code)
        self.l._collect_function_defs(c)
        self.l.dump_violations()
        self.assertEqual(self.l._functions, ['a', 'b', 'x', 'y'])