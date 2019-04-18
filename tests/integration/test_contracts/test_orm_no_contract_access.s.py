c = __Contract()

@seneca_export
def set_c():
    code = '''
@seneca_export
def a():
    print('gottem')    
'''
    c.submit(name='baloney', code=code, author='sys')
