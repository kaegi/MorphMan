import unittest
import test.all_tests
testSuite = test.all_tests.create_test_suite()
result = unittest.TextTestRunner().run(testSuite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
