import base64

exports = {'base64': base64}


def run_tests(_):
    '''
    >>> type(exports)
    <class 'dict'>
    '''
    import doctest, sys
    return doctest.testmod(sys.modules[__name__], extraglobs={**locals()})
