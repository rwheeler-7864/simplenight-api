import queue
import threading
from datetime import date
from decimal import Decimal
from time import sleep

from api import logger
from api.common.request_context import get_request_context
from api.models.models import SearchType, SearchResult, SearchEvent, Provider, HotelEvent

_SEARCH_EVENT_QUEUE = queue.SimpleQueue()
_HOTEL_EVENT_QUEUE = queue.SimpleQueue()


# Flush data in the background, for performance
def flush():
    def get_items(q: queue.SimpleQueue):
        while True:
            try:
                yield q.get(block=False)
            except queue.Empty:
                break

    while True:
        try:
            SearchEvent.objects.bulk_create(list(get_items(_SEARCH_EVENT_QUEUE)))
            HotelEvent.objects.bulk_create(list(get_items(_HOTEL_EVENT_QUEUE)))
        except Exception:
            logger.exception("Error while flushing analytics")

        sleep(5)


t1 = threading.Thread(name="Flush Analytics", target=flush, daemon=True)
t1.start()


def add_search_event(
    search_id: str,
    search_type: SearchType,
    start_date: date,
    end_date: date,
    search_input: str,
    search_result: SearchResult,
    elapsed_time: int,
    request_id: str,
):
    request_context = get_request_context()
    search_event = SearchEvent(
        search_event_data_id=search_id,
        organization=request_context.get_organization(),
        search_type=search_type,
        start_date=start_date,
        end_date=end_date,
        search_input=search_input,
        result=search_result,
        elapsed_time=elapsed_time,
        request_id=request_id,
    )

    _SEARCH_EVENT_QUEUE.put(search_event, False)
    logger.info(f"Queuing search event, queue size: {_SEARCH_EVENT_QUEUE.qsize()}")

    return search_event.search_event_data_id


def add_hotel_event(
    search_event_data_id: str,
    provider: Provider,
    provider_code: str,
    giata_code: str,
    total: Decimal,
    taxes: Decimal,
    base: Decimal,
    provider_total: Decimal,
    provider_base: Decimal,
    provider_taxes: Decimal,
):
    hotel_event_data = HotelEvent(
        search_event_data_id=search_event_data_id,
        provider=provider,
        provider_code=provider_code,
        giata_code=giata_code,
        total=total,
        taxes=taxes,
        base=base,
        provider_total=provider_total,
        provider_base=provider_base,
        provider_taxes=provider_taxes,
    )

    _HOTEL_EVENT_QUEUE.put(hotel_event_data)


class RepeatingTimer(threading.Thread):
    def __init__(self, interval_seconds, callback):
        super().__init__()
        self.interval_seconds = interval_seconds
        self.callback = callback

    def run(self):
        self.callback()
