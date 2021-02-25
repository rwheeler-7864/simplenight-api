from decimal import Decimal
from unittest.mock import patch

from api.hotel import markups
from api.tests import test_objects


def test_markup_room_rates():
    room_rate = test_objects.room_rate(rate_key="foo", total="100")

    with patch("uuid.uuid4", return_value="new-rate-key"):
        marked_up_rate = markups.markup_rate(room_rate)

    assert marked_up_rate.total.amount == Decimal("118")
    assert marked_up_rate.rate_key == "new-rate-key"
