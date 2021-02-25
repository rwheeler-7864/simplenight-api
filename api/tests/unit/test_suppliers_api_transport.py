from api.activities.adapters.suppliers_api import suppliers_api_util
from api.activities.adapters.suppliers_api.suppliers_api_transport import SuppliersApiTransport
from api.activities.adapters.tiqets.tiqets_transport import TiqetsTransport


def test_get_endpoint():
    endpoint = SuppliersApiTransport.Endpoint.DETAILS
    path_params = [str(123)]

    query_params = {
        "date_from": "2020-01-01",
        "date_to": "2020-02-01",
    }

    url = TiqetsTransport().get_endpoint(endpoint, path_params=path_params, query_params=query_params)
    expected = (
        "https://suppliers-api.qa-new.simplenight.com/v1/tiqets/details/123?date_from=2020-01-01&date_to=2020-02-01"
    )

    assert url == expected


def test_expand_schedule():
    availabilities = {
        "type": "ALWAYS",
        "label": "Whole Day Ticket",
        "days": ["MONDAY", "SUNDAY"],
        "times": ["12:00", "14:00"],
        "from": "2021-01-21",
        "to": "2021-01-31",
        "uuid": "a9d7fb1a-70d8-3284-9a7f-decfa5116467",
        "capacity": 20,
    }

    schedules = suppliers_api_util.expand_schedule(availabilities)

    assert len(schedules) == 6
