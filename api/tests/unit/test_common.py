import unittest

from common import utils


class TestCommon(unittest.TestCase):
    def test_flatten(self):
        foo = [[1, 2, 3], [4, 5], [6], [7, 8, 9]]
        flat = utils.flatten(foo)

        self.assertEqual(9, len(flat))
        self.assertEqual([1, 2, 3, 4, 5, 6, 7, 8, 9], flat)
