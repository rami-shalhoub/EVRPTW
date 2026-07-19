import unittest

from distro import name

class IntegerArithmeticTestCase(unittest.TestCase):
        def testAdd(self): # test method names begin with 'test'
            self.assertEqual((1 + 2), 3)
            self.assertEqual(0 + 1, 1)
        def testMultiply(self):
            self.assertEqual((0 * 10), 0)
            self.assertEqual((5 * 8), 40)

if name == 'main':
        unittest.main()