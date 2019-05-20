from unittest import TestCase
from contracting.execution import runtime

class TestRuntime(TestCase):
    def test_tracer_works_roughly(self):
        stamps = 1000
        runtime.rt.set_up(stmps=stamps, meter=True)
        a = 5
        used = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()
        self.assertLess(stamps -  used, stamps)

    def test_tracer_bypass_records_no_stamps(self):
        stamps = 1000
        runtime.rt.set_up(stmps=stamps, meter=False)
        a = 5
        used = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()
        self.assertEqual(stamps - used, stamps)