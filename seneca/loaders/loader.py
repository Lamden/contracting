import sys

from importlib.abc import Loader, ResourceLoader, PathEntryFinder, MetaPathFinder, Finder
from importlib.machinery import ModuleSpec
from importlib import invalidate_caches
from importlib.util import spec_from_file_location

from redis import Redis

class Database:
	def __init__(self, host='localhost', port=6379, delimiter=':'):
		self.conn = Redis(host=host, port=port)
		self.delimiter = delimiter

	def get_contract(self, name):
		return self.conn.hget(name, 'code').decode()

d = Database()

class DatabaseFinder(MetaPathFinder):
	def find_module(fullname, path, target=None):
		print('path: {}'.format(path))
		print(fullname)
		return DatabaseLoader()


class DatabaseLoader(Loader):
	def create_module(self, spec):
		# try to grab all of the subdirectories on a VK and stuff them in the spec
		#assert len(contracts) > 0
		#print(spec.__dict__)
		return None

	def find_spec(self, spec):
		pass

	def exec_module(self, module):
		# fetch the individual contract
		code = d.get_contract(module.__name__)
		exec(code, vars(module))

	def module_repr(self, module):
		return '<module {!r} (smart contract)>'.format(module.__name__)

	def get_data(self, path):
		print('p: ' + path)

def uninstall_builtins():
	sys.meta_path.clear()
	sys.path_hooks.clear()
	sys.path.clear()
	sys.path_importer_cache.clear()
	invalidate_caches()

def install_database_loader():
	#sys.path_hooks.append(DatabaseFinder)
	sys.meta_path.append(DatabaseFinder)

#uninstall_builtins()
install_database_loader()

import testing
print(testing.a)