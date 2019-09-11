from unittest import TestCase
from contracting.execution.executor import Context


class TestContext(TestCase):
    def test_get_state(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        self.assertEqual(c.get_state(), c.base_state)

    def test_get_state_after_added_state(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        new_state = {
            'caller': 'stuart',
            'signer': 'stuart',
            'this': 'contracts',
            'owner': 123
        }

        c.add_state(new_state)

        self.assertEqual(c.get_state(), new_state)

    def test_pop_state_doesnt_fail_if_none_added(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        c.pop_state()

        self.assertEqual(c.get_state(), c.base_state)

    def test_pop_state_removes_last_state(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        new_state = {
            'caller': 'stuart',
            'signer': 'stuart',
            'this': 'contracts',
            'owner': 123
        }

        c.add_state(new_state)

        self.assertEqual(c.get_state(), new_state)

        c.pop_state()

        self.assertEqual(c.get_state(), c.base_state)