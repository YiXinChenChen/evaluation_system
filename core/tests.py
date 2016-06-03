import unittest
# from django.test import TestCase

# Create your tests here.


class TestGenerateFromPhone(unittest.TestCase):
    def setUp(self):
        from core.invitation import generate_from_phone
        self.generate = generate_from_phone

    def test_phone_to_hash(self):
        phone = '15920488613'
        expected = '05GE6V55'

        self.assertEqual(self.generate(phone), expected)


class TestGenerateFromExecution(unittest.TestCase):
    def setUp(self):
        from core.invitation import generate_from_execution
        self.generate = generate_from_execution

    class FakeExecution():
        pass

    def test_phone_to_hash(self):
        execution = TestGenerateFromExecution.FakeExecution()
        execution.id = 1
        execution.phone = '15920488613'
        print self.generate(execution)
