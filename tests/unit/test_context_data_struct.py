from unittest import TestCase
from contracting.execution.runtime import Context


class TestContext(TestCase):
    def test_get_state(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        self.assertEqual(c._get_state(), c._base_state)

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

        c._add_state(new_state)

        self.assertEqual(c._get_state(), new_state)

    def test_pop_state_doesnt_fail_if_none_added(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        c._pop_state()

        self.assertEqual(c._get_state(), c._base_state)

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

        c._add_state(new_state)

        self.assertEqual(c._get_state(), new_state)

        c._pop_state()

        self.assertEqual(c._get_state(), c._base_state)

    def test_add_state_doesnt_work_if_this_is_same(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        new_state = {
            'caller': 'stuart',
            'signer': 'stuart',
            'this': 'contract',
            'owner': 123
        }

        c._add_state(new_state)

        self.assertEqual(c._get_state(), c._base_state)

    def test_properties_read(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        self.assertEqual(c._base_state['this'], c.this)
        self.assertEqual(c._base_state['caller'], c.caller)
        self.assertEqual(c._base_state['signer'], c.signer)
        self.assertEqual(c._base_state['owner'], c.owner)

    def test_properties_cant_be_written(self):
        c = Context(base_state={
            'caller': 'stu',
            'signer': 'stu',
            'this': 'contract',
            'owner': None
        })

        with self.assertRaises(Exception):
            c.this = 1

        with self.assertRaises(Exception):
            c.caller = 1

        with self.assertRaises(Exception):
            c.signer = 1

        with self.assertRaises(Exception):
            c.owner = 1
