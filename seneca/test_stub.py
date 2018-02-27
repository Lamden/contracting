'''
Seneca test import module, displays caller data.
'''

# seneca_internal injected global var only available within Seneca library modules, not in smart contracts
# seneca_internal.caller

def _print_caller_data():
    print(seneca_internal.caller)


exports = {
   'print_caller_data': _print_caller_data
}
