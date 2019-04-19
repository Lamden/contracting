fv = ForeignVariable(foreign_contract='test_orm_variable_contract', foreign_name='v')

@seneca_export
def set_fv(i):
    fv.set(i)

@seneca_export
def get_fv():
    return fv.get()
