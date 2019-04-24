old_time = time.datetime(2019, 1, 1)

@seneca_export
def gt():
    return ctx.now > old_time

@seneca_export
def lt():
    return ctx.now < old_time

@seneca_export
def eq():
    return ctx.now == old_time
