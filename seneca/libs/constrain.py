VALID_OPERATORS = ['=', '==', '>', '<', '>=', '<=']


def constrain(lhs, operator, rhs):
    """
    Basically our version of python's 'assert', which is intended to be used within smart contracts.
    :param lhs: 'Left Hand Side' of the equation. Must be a string denoting the redis key.
    :param operator: The equality operation. Must be '=', '>', '<', '>=', '<='
    :param rhs: 'Right Hand Side' of the equation
    :return: None
    """