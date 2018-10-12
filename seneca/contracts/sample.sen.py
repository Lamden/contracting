from seneca.contracts import good, okay

def good_call():
    good.one_you_can_export()
    okay.one_you_can_export()

def bad_call():
    good.one_you_cannot_export()
