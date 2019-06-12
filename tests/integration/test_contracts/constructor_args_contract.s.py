var1 = Variable()
var2 = Variable()

@construct
def seed(a, b):
    var1.set(a)
    var2.set(b)
    
@export
def get():
    a = var1.get()
    b = var2.get()
    return a, b