DB_TYPE = 'redis'

DB_URL = 'localhost'
DB_PORT = 6379
MASTER_DB = 0
DB_OFFSET = 1

DB_DELIMITER = ':'

# Number of available db's SenecaClients have available to get ahead on the next sub block while other sb's are
# awaiting a merge confirmation
NUM_CACHES = 4

# Resource limits
MEMORY_LIMIT = 32768  # 32kb
RECURSION_LIMIT = 1024

DELIMITER = ':'
CODE_KEY = '__code__'
TYPE_KEY = '__type__'
AUTHOR_KEY = '__author__'
OWNER_KEY = '__owner__'
TIME_KEY = '__submitted__'
INDEX_SEPARATOR = '.'

DECIMAL_PRECISION = 64

PRIVATE_METHOD_PREFIX = '__'
EXPORT_DECORATOR_STRING = 'export'
INIT_DECORATOR_STRING = 'construct'
INIT_FUNC_NAME = '__{}'.format(PRIVATE_METHOD_PREFIX)
VALID_DECORATORS = {EXPORT_DECORATOR_STRING, INIT_DECORATOR_STRING}

ORM_CLASS_NAMES = {'Variable', 'Hash', 'ForeignVariable', 'ForeignHash'}

MAX_HASH_DIMENSIONS = 16
MAX_KEY_SIZE = 1024

READ_COST_PER_BYTE = 3
WRITE_COST_PER_BYTE = 25

STAMPS_PER_TAU = 500
