import sys

from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec
from importlib import invalidate_caches
from importlib.util import spec_from_file_location

from redis import Redis

class Database:
	def __init__(self, host='localhost', port=6379, delimiter=':'):
		self.conn = Redis(host=host, port=port)
		self.delimiter = delimiter

	def get_contracts(self, name):
		# Scans through all contracts on Redis with the provided prefix.
		# Contracts are stored as <name>:*
		contracts = []
		cursor = -1
		while cursor != 0:
			cursor = 0
			# Cursor will be returned as 0 if there are not many contracts stored
			cursor, _contracts = self.conn.scan(cursor, '{}{}*'.format(name, self.delimiter))
			contracts.extend(_contracts)
			print(cursor)
		return contracts

d = Database()

class DatabaseFinder(MetaPathFinder):
	def find_module(fullname, path):
		return DatabaseLoader()


class DatabaseLoader(Loader):
	def create_module(self, spec):
		# try to grab all of the subdirectories on a VK and stuff them in the spec

		print(spec.name)
		#assert len(contracts) > 0

		return None

	def exec_module(self, module):
		print(dir(module))
		print(module.__doc__)
		print(module.__loader__)
		print(module.__name__)
		print(module.__package__)
		print(module.__spec__)

		# fetch the individual contract
		#exec("poopoo = 1", vars(module))

	def module_repr(self, module):
		return '<module {!r} (smart contract)>'.format(module.__name__)

def uninstall_builtins():
	sys.meta_path.clear()
	sys.path_hooks.clear()
	sys.path.clear()
	sys.path_importer_cache.clear()
	invalidate_caches()

def install_database_loader():
	sys.path_hooks.append(DatabaseFinder)
	sys.meta_path.insert(0, DatabaseFinder)

uninstall_builtins()
install_database_loader()