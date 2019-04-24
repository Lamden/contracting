old_time = time.datetime(2019, 1, 1)

@seneca_export
def ha():
    old_time._datetime = None
    return old_time
