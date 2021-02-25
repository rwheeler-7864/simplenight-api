from decimal import Decimal
from unittest.mock import patch, MagicMock

from api.hotel import price_verification_service
from api.tests import test_objects
from api.tests.unit.simplenight_test_case import SimplenightTestCase


class TestPriceVerificationService(SimplenightTestCase):
    def test_price_verification_default_model(self):
        """Tests price verification with the default comparison model"""

        hotel = test_objects.hotel()
        original_room_rate = test_objects.room_rate(rate_key="key1", total="100")
        verified_room_rate = test_objects.room_rate(rate_key="key1", total="100")

        mock_adapter = MagicMock()
        mock_adapter.recheck.return_value = verified_room_rate
        with patch("api.hotel.adapters.adapter_service.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter
            price_change = price_verification_service.recheck(hotel.provider, original_room_rate)

        assert price_change.is_exact_price is True
        assert price_change.is_allowed_change is True

    def test_price_verification_default_model_price_change(self):
        """Tests the default price verification model when a price change occurs"""

        hotel = test_objects.hotel()
        original_room_rate = test_objects.room_rate(rate_key="key1", total="100")
        verified_room_rate = test_objects.room_rate(rate_key="key1", total="125.50")

        mock_adapter = MagicMock()
        mock_adapter.recheck.return_value = verified_room_rate
        with patch("api.hotel.adapters.adapter_service.get_adapter") as mock_get_adapter:
            mock_get_adapter.return_value = mock_adapter
            price_change = price_verification_service.recheck(hotel.provider, original_room_rate)

        assert price_change.is_exact_price is False
        assert price_change.is_allowed_change is False
        assert price_change.price_difference == Decimal("25.50")
