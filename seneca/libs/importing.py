import types
from seneca.engine.interpret.parser import Parser


def import_contract(contract_name):
    contract = Parser.executor.get_contract(contract_name)
    module = types.ModuleType(contract_name)
    Parser.parser_scope['rt']['contract'] = contract_name
    Parser.executor.execute(contract['code_obj'])
    return module
