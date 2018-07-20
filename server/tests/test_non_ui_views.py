"""Beginning of the test setup for non_ui_views"""

from django.test import TestCase

from server.models import *
from server import non_ui_views


class CheckinDataTest(TestCase):
    """Test the checkin from client"""

    def test_checkin_memory_value_conversion(self):
        """Ensure conversion of memory to memory_kb is correct"""

        # hash of string description to number of KB
        memconv = {'4 GB': 4194304,
                   '8 GB': 8388608,
                   '1 TB': 1073741824}

        # pass each value and check proper value returned
        test_machine = Machine(serial='testtesttest123')
        for key in memconv:
            test_machine.memory = key
            self.assertEqual(non_ui_views.process_memory(test_machine), memconv[key])
