from functools import partial

# Note: functools partial is not safe for this application
# It preserves function and arguments and both can be extracted
# We want application to be irreversable
def partial(f, *args, **kwargs):
    def ret(*inner_args, **inner_kwargs):
        all_args = args + inner_args
        all_kwargs = {**inner_kwargs, **kwargs} # partially applied kwargs take precedence
        return f()
    # Todo: this may not be safe either, must disable all methods except call
    return ret
