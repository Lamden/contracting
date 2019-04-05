from seneca.engine.interpreter.linter import Linter
import ast

def test_linter():
    # log = get_logger("TestSenecaLinter")
    with open('stubucks.py', 'r') as myfile:
        data=myfile.read()
   
    print("raghu code: \n{}".format(data))
    ptree = ast.parse(data)
    linter = Linter()
    status = linter.check(ptree)
    if status:
        print("Success!")
    else:
        print("Failed!")



if __name__ == '__main__':
    test_linter()
