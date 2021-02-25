from typing import List
from api.carey.models.carey_api_model import RateInquiryRequest
from api.carey.models.carey_api_model import (
    QuoteResponse,
    VehicleDetails,
    ChargeDetails,
    ChargeItem,
    Reference,
    TotalAmount,
    AdditionalInfo,
    NameType,
    TotalChargeType,
    Location,
    CountryNameType,
    Airport,
    StateProvType,
    BookingResponseLocation,
    BookResponse,
    CancelResponse,
    AddtionalInfoItem,
)


class CareyParser:
    def __init__(self):
        super().__init__()

    def parse_quotes(self, quotes_datas, request: RateInquiryRequest) -> List[QuoteResponse]:
        quote_details = []
        for quote_data in quotes_datas:
            chargeItemsDetails = quote_data["Reference"]["TPA_Extensions"]["ChargeDetails"]["Charges"]["Items"][
                "ItemVariable"
            ]
            chargeItemsInfo = []
            addtionalInfo = []
            additionals = quote_data["Reference"]["TPA_Extensions"]["AdditionalInfo"]["DisplayMessage"]
            for items in additionals:
                addtionalItemInfo = AddtionalInfoItem(message=items["_value_1"])
                addtionalInfo.append(addtionalItemInfo)
            for chargeItemsDetail in chargeItemsDetails:
                chargeItemInfo = ChargeItem(
                    itemName=chargeItemsDetail["ItemName"],
                    itemDescription=chargeItemsDetail["ItemDescription"],
                    itemUnit=chargeItemsDetail["ItemUnit"]["Unit"],
                    itemUnitValue=chargeItemsDetail["ItemUnit"]["_value_1"],
                    itemUnitPrice=chargeItemsDetail["ItemUnitPrice"]["_value_1"],
                    itemUnitPriceCurrency=chargeItemsDetail["ItemUnitPrice"]["Currency"],
                    readBack=chargeItemsDetail["ReadBack"],
                    sequenceNumber=chargeItemsDetail["SequenceNumber"],
                )
                chargeItemsInfo.append(chargeItemInfo)

            quote_detail = QuoteResponse(
                pickUpDate=request.dateTime,
                pickUpLoacation=request.pickUpLoacation,
                dropOffLocation=request.dropOffLocation,
                vehicleDetails=VehicleDetails(
                    vehicleName=quote_data["Shuttle"][0]["Vehicle"]["Type"]["_value_1"],
                    vehicleCode=quote_data["Shuttle"][0]["Vehicle"]["Type"]["Description"],
                    vehicleDescriptionDetail=quote_data["Shuttle"][0]["Vehicle"]["Type"]["DescriptionDetail"],
                    maxPassengers=quote_data["Shuttle"][0]["Vehicle"]["VehicleSize"]["MaxPassengerCapacity"],
                    maxBags=quote_data["Shuttle"][0]["Vehicle"]["VehicleSize"]["MaxBaggageCapacity"],
                ),
                chargeDetails=ChargeDetails(
                    readBack=quote_data["Reference"]["TPA_Extensions"]["ChargeDetails"]["Charges"]["ReadBack"],
                    billingType=quote_data["Reference"]["TPA_Extensions"]["ChargeDetails"]["Charges"]["BillingType"],
                ),
                chargeItems=chargeItemsInfo,
                reference=Reference(
                    estimatedDistance=quote_data["Reference"]["TPA_Extensions"]["EstimatedDistance"],
                    estimatedTime=quote_data["Reference"]["TPA_Extensions"]["EstimatedTime"],
                ),
                total=TotalAmount(
                    totalAmountValue=quote_data["TotalCharge"]["RateTotalAmount"],
                    totalAmountCurrency=quote_data["Reference"]["TPA_Extensions"]["TotalAmount"]["Currency"],
                    totalAmountDescription=quote_data["Reference"]["TPA_Extensions"]["TotalAmount"]["_value_1"],
                ),
                additional=AdditionalInfo(
                    notice=quote_data["Reference"]["TPA_Extensions"]["Notice"],
                    garageToGarageEstimate=quote_data["Reference"]["TPA_Extensions"]["GarageToGarageEstimate"],
                    additionalInfo=addtionalInfo,
                ),
                special=request.special,
                tripType=request.tripType,
                passengers=request.passengers,
                bags=request.bags,
                flightInfo=request.flightInfo,
            )

            quote_details.append(quote_detail)

        return quote_details

    def parse_booking_response(self, booking_response_data) -> BookResponse:
        booking_data = booking_response_data["Reservation"][0]
        booking_pickup_address = booking_data["Service"]["Locations"]["Pickup"]["Address"]
        booking_pickup_airport = booking_data["Service"]["Locations"]["Pickup"]["AirportInfo"]
        booking_dropoff_address = booking_data["Service"]["Locations"]["Dropoff"]["Address"]
        booking_dropoff_airport = booking_data["Service"]["Locations"]["Dropoff"]["AirportInfo"]
        pickUpaddress = None
        pickUpairport = None
        pickUpairline = None
        dropOffaddress = None
        dropOffairport = None
        dropOffairline = None
        if booking_pickup_address:
            pickUpaddress = Location(
                latitude=booking_pickup_address["Latitude"],
                longitude=booking_pickup_address["Longitude"],
                locationName=booking_pickup_address["LocationName"],
                addressLine=booking_pickup_address["AddressLine"][0],
                cityName=booking_pickup_address["CityName"],
                postalCode=booking_pickup_address["PostalCode"],
                stateProv=StateProvType(
                    value=booking_pickup_address["StateProv"]["_value_1"],
                    stateCode=booking_pickup_address["StateProv"]["StateCode"],
                ),
                countryName=CountryNameType(
                    value=booking_pickup_address["CountryName"]["_value_1"],
                    stateCode=booking_pickup_address["CountryName"]["Code"],
                ),
                airport=None,
                airportCode=None,
                trainStation=None,
            )
        elif booking_pickup_airport:
            pickUpairport = Airport(
                airportName=booking_pickup_airport["Departure"]["AirportName"],
                airportCode=booking_pickup_airport["Departure"]["LocationCode"],
            )

        if booking_dropoff_address:
            dropOffaddress = Location(
                latitude=booking_dropoff_address["Latitude"],
                longitude=booking_dropoff_address["Longitude"],
                locationName=booking_dropoff_address["LocationName"],
                addressLine=booking_dropoff_address["AddressLine"][0],
                cityName=booking_dropoff_address["CityName"],
                postalCode=booking_dropoff_address["PostalCode"],
                stateProv=StateProvType(
                    value=booking_dropoff_address["StateProv"]["_value_1"],
                    stateCode=booking_dropoff_address["StateProv"]["StateCode"],
                ),
                countryName=CountryNameType(
                    value=booking_dropoff_address["CountryName"]["_value_1"],
                    stateCode=booking_dropoff_address["CountryName"]["Code"],
                ),
                airport=None,
                airportCode=None,
                trainStation=None,
            )
        elif booking_dropoff_airport:
            dropOffairport = Airport(
                airportName=booking_dropoff_airport["Departure"]["AirportName"],
                airportCode=booking_dropoff_airport["Departure"]["LocationCode"],
            )

        booking_response = BookResponse(
            confirm_id=booking_data["Confirmation"]["ID"],
            email=booking_data["Passenger"]["Primary"]["Email"][0]["_value_1"],
            name=NameType(
                firstName=booking_data["Passenger"]["Primary"]["PersonName"]["GivenName"][0],
                lastName=booking_data["Passenger"]["Primary"]["PersonName"]["Surname"],
            ),
            pickupDate=booking_data["Service"]["Locations"]["Pickup"]["DateTime"],
            pickUpLocation=BookingResponseLocation(address=pickUpaddress, airport=pickUpairport, airline=pickUpairline),
            dropOffLocation=BookingResponseLocation(
                address=dropOffaddress, airport=dropOffairport, airline=dropOffairline
            ),
            total=TotalChargeType(
                total=booking_response_data["TPA_Extensions"]["TotalAmount"]["_value_1"],
                currency=booking_response_data["TPA_Extensions"]["TotalAmount"]["Currency"],
            ),
        )
        return booking_response

    def parse_find_response(self, find_response_data) -> BookResponse:
        find_data = find_response_data["DetailedReservation"][0]
        find_pickup_address = find_data["Service"]["Locations"]["Pickup"]["Address"]
        find_pickup_airport = find_data["Service"]["Locations"]["Pickup"]["AirportInfo"]
        find_dropoff_address = find_data["Service"]["Locations"]["Dropoff"]["Address"]
        find_dropoff_airport = find_data["Service"]["Locations"]["Dropoff"]["AirportInfo"]
        pickUpaddress = None
        pickUpairport = None
        pickUpairline = None
        dropOffaddress = None
        dropOffairport = None
        dropOffairline = None
        if find_pickup_address:
            pickUpaddress = Location(
                latitude=find_pickup_address["Latitude"],
                longitude=find_pickup_address["Longitude"],
                locationName=find_pickup_address["LocationName"],
                addressLine=find_pickup_address["AddressLine"][0],
                cityName=find_pickup_address["CityName"],
                postalCode=find_pickup_address["PostalCode"],
                stateProv=StateProvType(
                    value=find_pickup_address["StateProv"]["_value_1"],
                    stateCode=find_pickup_address["StateProv"]["StateCode"],
                ),
                countryName=CountryNameType(
                    value=find_pickup_address["CountryName"]["_value_1"],
                    stateCode=find_pickup_address["CountryName"]["Code"],
                ),
                airport=None,
                airportCode=None,
                trainStation=None,
            )
        elif find_pickup_airport:
            pickUpairport = Airport(
                airportName=find_pickup_airport["Departure"]["AirportName"],
                airportCode=find_pickup_airport["Departure"]["LocationCode"],
            )

        if find_dropoff_address:
            dropOffaddress = Location(
                latitude=find_dropoff_address["Latitude"],
                longitude=find_dropoff_address["Longitude"],
                locationName=find_dropoff_address["LocationName"],
                addressLine=find_dropoff_address["AddressLine"][0],
                cityName=find_dropoff_address["CityName"],
                postalCode=find_dropoff_address["PostalCode"],
                stateProv=StateProvType(
                    value=find_dropoff_address["StateProv"]["_value_1"],
                    stateCode=find_dropoff_address["StateProv"]["StateCode"],
                ),
                countryName=CountryNameType(
                    value=find_dropoff_address["CountryName"]["_value_1"],
                    stateCode=find_dropoff_address["CountryName"]["Code"],
                ),
                airport=None,
                airportCode=None,
                trainStation=None,
            )
        elif find_dropoff_airport:
            dropOffairport = Airport(
                airportName=find_dropoff_airport["Departure"]["AirportName"],
                airportCode=find_dropoff_airport["Departure"]["LocationCode"],
            )

        find_response = BookResponse(
            confirm_id=find_data["Confirmation"]["ID"],
            email=find_data["Passenger"]["Primary"]["Email"][0]["_value_1"],
            name=NameType(
                firstName=find_data["Passenger"]["Primary"]["PersonName"]["GivenName"][0],
                lastName=find_data["Passenger"]["Primary"]["PersonName"]["Surname"],
            ),
            pickupDate=find_data["Service"]["Locations"]["Pickup"]["DateTime"],
            pickUpLocation=BookingResponseLocation(address=pickUpaddress, airport=pickUpairport, airline=pickUpairline),
            dropOffLocation=BookingResponseLocation(
                address=dropOffaddress, airport=dropOffairport, airline=dropOffairline
            ),
            total=TotalChargeType(
                total=find_response_data["TPA_Extensions"]["TotalAmount"]["_value_1"],
                currency=find_response_data["TPA_Extensions"]["TotalAmount"]["Currency"],
            ),
            sequenceNmbr=find_response_data["SequenceNmbr"],
            version=find_response_data["Version"],
        )

        return find_response

    def parse_cancel_response(self, cancel_response_data) -> CancelResponse:
        cancelID = cancel_response_data["Reservation"]["CancelConfirmation"]["UniqueID"]["ID"]
        reservationID = cancel_response_data["Reservation"]["CancelConfirmation"]["UniqueID"]["ID_Context"]
        cancel_pickup_address = cancel_response_data["Reservation"]["ReservationInfo"]["ServiceInfo"]["Location"][
            "Pickup"
        ]["Address"]
        cancel_pickup_airport = cancel_response_data["Reservation"]["ReservationInfo"]["ServiceInfo"]["Location"][
            "Pickup"
        ]["AirportInfo"]
        pickUpaddress = None
        pickUpairport = None
        pickUpairline = None
        if cancel_pickup_address:
            pickUpaddress = Location(
                latitude=cancel_pickup_address["Latitude"],
                longitude=cancel_pickup_address["Longitude"],
                locationName=cancel_pickup_address["LocationName"],
                addressLine=cancel_pickup_address["AddressLine"][0],
                cityName=cancel_pickup_address["CityName"],
                postalCode=cancel_pickup_address["PostalCode"],
                stateProv=StateProvType(
                    value=cancel_pickup_address["StateProv"]["_value_1"],
                    stateCode=cancel_pickup_address["StateProv"]["StateCode"],
                ),
                countryName=CountryNameType(
                    value=cancel_pickup_address["CountryName"]["_value_1"],
                    stateCode=cancel_pickup_address["CountryName"]["Code"],
                ),
                airport=None,
                airportCode=None,
                trainStation=None,
            )
        elif cancel_pickup_airport:
            pickUpairport = Airport(
                airportName=cancel_pickup_airport["Departure"]["AirportName"],
                airportCode=cancel_pickup_airport["Departure"]["LocationCode"],
            )

        cancel_response = CancelResponse(
            cancel_id=cancelID,
            reservation_id=reservationID,
            name=NameType(
                firstName=cancel_response_data["Reservation"]["ReservationInfo"]["Passengers"]["Primary"]["PersonName"][
                    "GivenName"
                ][0],
                lastName=cancel_response_data["Reservation"]["ReservationInfo"]["Passengers"]["Primary"]["PersonName"][
                    "Surname"
                ],
            ),
            pickUpdate=cancel_response_data["Reservation"]["ReservationInfo"]["ServiceInfo"]["Location"]["Pickup"][
                "DateTime"
            ],
            pickUpLocation=BookingResponseLocation(address=pickUpaddress, airport=pickUpairport, airline=pickUpairline),
        )
        return cancel_response
