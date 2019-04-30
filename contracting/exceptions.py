
class SenecaError(Exception):
    """
    The base exception for Seneca. The fmt directive
    will be overloaded by the inheriting classes

    :ivar msg: The message associated with the error
    """
    fmt = 'An unspecified error occurred'

    def __init__(self, **kwargs):
        msg = self.fmt.format(**kwargs)
        Exception.__init__(self, msg)
        self.kwargs = kwargs


class DatabaseDriverNotFound(SenecaError):
    """
    Could not find the specified database driver when
    looking for it

    :ivar driver: The name of the database driver the
                  the user attempted to load
    :ivar known_drivers: The list of known drivers
                         currently supported in Seneca
    """
    fmt = "Unknown database driver '{driver}', known drivers '{known_drivers}'"


class ContractExists(SenecaError):
    """
    When attempting to set a contract, found that it
    already exists in the database

    :ivar contract_name: The name of the contract
                         submitted.
    """
    fmt = "Contract with name '{contract_name}' already exists in the database"


class CompilationException(Exception):
    pass


class SenecaException(Exception):
    """
    Base exeception to be returned by default from inside contracting contracts
    """
