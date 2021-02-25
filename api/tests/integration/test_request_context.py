from api.models.models import Feature
from api.common.request_context import get_config_bool, get_config
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestRequestContext(SimplenightTestCase):
    def test_configurations(self):
        self.stub_feature(Feature.TEST_MODE, "true")
        self.assertTrue(get_config_bool(Feature.TEST_MODE))

        self.stub_feature(Feature.TEST_MODE, "false")
        self.assertFalse(get_config_bool(Feature.TEST_MODE))

        self.stub_feature(Feature.TEST_MODE, "true")
        self.assertTrue(get_config_bool(Feature.TEST_MODE))

        self.stub_feature(Feature.ENABLED_ADAPTERS, "foo")
        self.assertEqual("foo", get_config(Feature.ENABLED_ADAPTERS))
