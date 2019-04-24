old_time = datetime(2019, 1, 1)

@seneca_export
def gt():
    return now > old_time

@seneca_export
def lt():
    return now < old_time

@seneca_export
def eq():
    return now == old_time
