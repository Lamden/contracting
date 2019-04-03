from importlib.abc import Loader, MetaPathFinder


class DatabaseFinder(MetaPathFinder):
    def find_module(self, fullname, path):
        pass


class DatabaseLoader(Loader):
    def create_module(self, spec):
        pass

    def exec_module(self, module):
        pass

    def load_module(self, fullname):
        pass

    def module_repr(self, module):
        pass