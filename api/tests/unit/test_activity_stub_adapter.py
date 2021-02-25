import unittest
from datetime import date

from api.activities.adapters.stub_activity_adapter import StubActivityAdapter
from api.multi.multi_product_models import ActivitySearch


class TestActivityStubAdapter(unittest.TestCase):
    def test_search_by_id(self):
        adapter = StubActivityAdapter()
        results = adapter.search_by_id(
            ActivitySearch(begin_date=date(2020, 1, 1), end_date=date(2020, 1, 5), adults=1, children=0)
        )

        self.assertIsNotNone(results)
        print(results)
