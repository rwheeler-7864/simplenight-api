import uuid
from datetime import date, datetime
from typing import Union, List

from lxml import etree

from api.hotel.google_pricing.google_pricing_models import GooglePricingItineraryQuery
from api.hotel.models.hotel_api_model import SimplenightHotel
from api.models.models import PhoneType


def deserialize(xmlstr: Union[str, bytes]) -> GooglePricingItineraryQuery:
    if isinstance(xmlstr, str):
        xmlstr = xmlstr.encode("utf-8")

    parser = etree.XMLParser(recover=True, encoding="utf-8")
    doc = etree.fromstring(xmlstr, parser)

    return GooglePricingItineraryQuery(
        checkin=date.fromisoformat(doc.find("Checkin").text),
        nights=int(doc.find("Nights").text),
        hotel_codes=list(map(lambda x: x.text, doc.findall("PropertyList/Property"))),
    )


def serialize(query: GooglePricingItineraryQuery, hotels: List[SimplenightHotel]) -> str:
    transaction = etree.Element("Transaction")
    transaction.attrib["timestamp"] = str(datetime.now())
    transaction.attrib["id"] = str(uuid.uuid4())

    for hotel in hotels:
        result = etree.Element("Result")
        result.append(_get_element("Property", hotel.hotel_id, cdata=True))
        result.append(_get_element("Checkin", str(hotel.start_date), cdata=False))
        result.append(_get_element("Nights", str(query.nights), cdata=False))

        lowest_rate_room = min(hotel.room_types, key=lambda x: x.total.amount)
        result.append(_get_element("RoomID", "lowest_rate", cdata=True))

        base_rate = etree.Element("Baserate")
        base_rate.attrib["currency"] = lowest_rate_room.total_base_rate.currency
        base_rate.attrib["all_inclusive"] = "false"
        base_rate.text = str(lowest_rate_room.total_base_rate.amount)
        result.append(base_rate)

        tax = etree.Element("Tax")
        tax.attrib["currency"] = lowest_rate_room.total_tax_rate.currency
        tax.text = str(lowest_rate_room.total_tax_rate.amount)
        result.append(tax)

        other_fees = etree.Element("OtherFees")
        other_fees.attrib["currency"] = lowest_rate_room.total.currency
        other_fees.text = "0"
        result.append(other_fees)
        if lowest_rate_room.postpaid_fees:
            other_fees.text = str(lowest_rate_room.postpaid_fees.total.amount)

        transaction.append(result)

    return etree.tostring(transaction)


def serialize_property_list(provider_hotels):
    root = etree.Element("listings")
    root.append(_get_element("language", "en"))

    for provider_hotel in provider_hotels:
        listing = etree.Element("listing")
        listing.append(_get_element("id", provider_hotel.provider_code))
        listing.append(_get_element("name", provider_hotel.hotel_name, cdata=True))

        address = etree.Element("address")
        address.attrib["format"] = "simple"
        address.append(_get_element("component", provider_hotel.address_line_1, name="addr1", cdata=True))
        if provider_hotel.address_line_2:
            address.append(_get_element("component", provider_hotel.address_line_2, name="addr2", cdata=True))

        address.append(_get_element("component", provider_hotel.city_name, name="city"))
        address.append(_get_element("component", provider_hotel.postal_code, name="postal_code"))
        address.append(_get_element("component", provider_hotel.state, name="province"))
        listing.append(address)

        listing.append(_get_element("country", provider_hotel.country_code))
        listing.append(_get_element("latitude", str(provider_hotel.latitude)))
        listing.append(_get_element("longitude", str(provider_hotel.longitude)))
        phones = provider_hotel.phone.all()

        if not provider_hotel.latitude or not provider_hotel.longitude or not phones:
            continue

        phone_type_map = {
            PhoneType.VOICE: "main",
            PhoneType.FAX: "fax",
        }

        for phone in phones:
            phone_type = phone_type_map.get(phone.type)
            phone_number = phone.phone_number
            listing.append(_get_element("phone", phone_number, type=phone_type))

        root.append(listing)

    return etree.tostring(root, encoding="utf-8", xml_declaration=True)


def _get_element(tag, content, cdata=False, **attribs):
    element = etree.Element(tag)
    if content and content != "None":  # TODO: Fix "None" string in source data
        content = content.strip()
        if cdata:
            element.text = etree.CDATA(content)
        else:
            element.text = content

    for key, value in attribs.items():
        element.attrib[key] = value

    return element
