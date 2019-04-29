import secrets
from seneca.db.driver import ContractDriver
from seneca.execution.executor import Executor

from pyinstrument import Profiler

def submission_kwargs_for_file(f):
    # Get the file name only by splitting off directories
    split = f.split('/')
    split = split[-1]

    # Now split off the .s
    split = split.split('.')
    contract_name = split[0]

    with open(f) as file:
        contract_code = file.read()

    return {
        'name': contract_name,
        'code': contract_code,
    }


TEST_SUBMISSION_KWARGS = {
    'sender': 'stu',
    'contract_name': 'submission',
    'function_name': 'submit_contract'
}


d = ContractDriver()
d.flush()

with open('../../seneca/contracts/submission.s.py') as f:
    contract = f.read()

d.set_contract(name='submission',
                    code=contract,
                    author='sys')
d.commit()

recipients = [secrets.token_hex(16) for _ in range(1000)]


e = Executor()

e.execute(**TEST_SUBMISSION_KWARGS,
          kwargs=submission_kwargs_for_file('../integration/test_contracts/erc20_clone.s.py'))


import datetime

now = datetime.datetime.now()

# profiler = Profiler()
# profiler.start()
for r in recipients:
    e.execute(sender='stu',
              contract_name='erc20_clone',
              function_name='transfer',
              kwargs={
                  'amount': 1,
                  'to': r
              })
# profiler.stop()

print(datetime.datetime.now() - now)
d.flush()

# print(profiler.last_session.duration)
# print(profiler.output_text(unicode=True, color=True, show_all=True))

