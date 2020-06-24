from unittest import TestCase
from contracting.execution import runtime


class TestRuntime(TestCase):
    def tearDown(self):
        runtime.rt.tracer.stop()
        runtime.rt.clean_up()

    def test_tracer_works_roughly(self):
        stamps = 1000
        runtime.rt.set_up(stmps=stamps, meter=True)
        a = 5
        runtime.rt.tracer.stop()
        used = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()
        self.assertLess(stamps - used, stamps)

    def test_tracer_bypass_records_no_stamps(self):
        stamps = 1000
        runtime.rt.set_up(stmps=stamps, meter=False)
        a = 5
        b = 5
        runtime.rt.tracer.stop()
        used = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()
        self.assertEqual(stamps - used, stamps)

    def test_arbitrary_modification_of_stamps_works(self):
        stamps = 1000
        sub = 500
        runtime.rt.set_up(stmps=stamps, meter=True)
        globals()['__contract__'] = True
        a = 5
        globals()['__contract__'] = False
        runtime.rt.tracer.stop()
        used_1 = runtime.rt.tracer.get_stamp_used()
        runtime.rt.tracer.set_stamp(stamps - sub)
        used_2 = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()

        print(used_1, used_2)

    def test_starting_and_stopping_tracer_works_roughly(self):
        stamps = 1000
        runtime.rt.set_up(stmps=stamps, meter=True)
        globals()['__contract__'] = True
        a = 5
        b = 5
        c = 5
        d = 5
        e = 5
        globals()['__contract__'] = False
        runtime.rt.tracer.stop()
        used_1 = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()

        stamps = 1000
        runtime.rt.set_up(stmps=stamps, meter=True)
        a = 5
        b = 5
        runtime.rt.tracer.stop()
        c = 5
        d = 5
        e = 5
        runtime.rt.tracer.stop()
        used_2 = runtime.rt.tracer.get_stamp_used()
        runtime.rt.clean_up()

        self.assertGreater(used_1, used_2)

    def test_modifying_stamps_during_tracing(self):
        stamps = 10000
        runtime.rt.set_up(stmps=stamps, meter=True)
        a = 5
        b = 5
        runtime.rt.tracer.stop()
        c = 5
        d = 5
        e = 5
        runtime.rt.clean_up()
        used_1 = runtime.rt.tracer.get_stamp_used()

        stamps = 5000
        runtime.rt.set_up(stmps=stamps, meter=True)
        a = 5
        b = 5
        runtime.rt.tracer.stop()
        used_1 = runtime.rt.tracer.get_stamp_used()
        runtime.rt.set_up(stmps=stamps - used_1, meter=True)
        c = 5
        d = 5
        e = 5
        runtime.rt.clean_up()
        used_2 = runtime.rt.tracer.get_stamp_used()

        print(used_1, used_2)

    def test_add_exists(self):
        stamps = 1000

        runtime.rt.set_up(stmps=stamps, meter=True)

        runtime.rt.tracer.add_cost(900)
        runtime.rt.tracer.stop()

        used_1 = runtime.rt.tracer.get_stamp_used()

        runtime.rt.clean_up()
        print(used_1)