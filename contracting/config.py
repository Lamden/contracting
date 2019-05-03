DB_TYPE = 'redis'

DB_URL = 'localhost'
DB_PORT = 6379
MASTER_DB = 0
DB_OFFSET = 1

DB_DELIMITER = ':'

# Number of available db's SenecaClients have available to get ahead on the next sub block while other sb's are
# awaiting a merge confirmation
NUM_CACHES = 4

# Set timeouts for CR
EXEC_TIMEOUT = 14  # Timeout for other subblocks finishing exec
CR_TIMEOUT = 14  # Timeout for other subblocks finishing CR
BLOCK_TIMEOUT = 30  # Timeout to wait for CRCache to be written to master
CLEAN_TIMEOUT = 30  # Timeout to wait for DBs to synchronize their reset calls
AVAIL_DB_TIMEOUT = 60
POLL_INTERVAL = 0.1

# Number of sb's to queue up if we run out of caches
MAX_SB_QUEUE_SIZE = 8

# Resource limits
MEMORY_LIMIT = 32768  # 32kb
RECURSION_LIMIT = 1024

DELIMITER = ':'
CODE_KEY = '__code__'
TYPE_KEY = '__type__'
AUTHOR_KEY = '__author__'
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
