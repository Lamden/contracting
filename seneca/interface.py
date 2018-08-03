from seneca.engine.storage.mysql_executer import Executer
from seneca.engine.storage.mysql_spits_executer import Executer as Spits
# a
class Driver:
    def __init__(self, username, password, database, port):
        self.ex = None
        self.spex = None

    def submit(self, smart_contract):
        pass

    def flush(self):
        pass

    def load_director(self, directory):
        pass