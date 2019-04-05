from seneca.execution.linter import Linter
import ast

def test_linter():
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


