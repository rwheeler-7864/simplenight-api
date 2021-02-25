from decimal import Decimal
from typing import Optional, List
from api.common.common_models import SimplenightModel


class StateProvType(SimplenightModel):
    value: str
    stateCode: str


class CountryNameType(SimplenightModel):
    value: str
    stateCode: str


class FlightInfo(SimplenightModel):
    flightDate: str
    flightNum: str
    flightCode: str


class Location(SimplenightModel):
    latitude: Decimal
    longitude: Decimal
    locationName: str
    addressLine: Optional[str]
    cityName: Optional[str]
    postalCode: Optional[str]
    stateProv: object
    countryName: Optional[CountryNameType]
    airport: Optional[bool]
    airportCode: Optional[str]
    trainStation: Optional[bool]


class RateInquiryRequest(SimplenightModel):
    dateTime: str
    passengers: int
    bags: int
    tripType: Optional[str] = "Point-To-Point"
    pickUpLoacation: Location
    flightInfo: Optional[FlightInfo]
    dropOffLocation: Location
    special: Optional[str]


class VehicleDetails(SimplenightModel):
    vehicleName: Optional[str]
    vehicleCode: Optional[str]
    vehicleDescriptionDetail: Optional[str]
    maxPassengers: Optional[str]
    maxBags: Optional[str]


class Reference(SimplenightModel):
    estimatedDistance: Optional[str]
    estimatedTime: Optional[str]


class ChargeDetails(SimplenightModel):
    readBack: Optional[str]
    billingType: Optional[str]


class ChargeItem(SimplenightModel):
    itemName: Optional[str]
    itemDescription: Optional[str]
    itemUnit: Optional[str]
    itemUnitValue: Optional[Decimal]
    itemUnitPrice: Optional[Decimal]
    itemUnitPriceCurrency: Optional[str]
    readBack: Optional[str]
    sequenceNumber: Optional[str]


class TotalAmount(SimplenightModel):
    totalAmountValue: Decimal
    totalAmountCurrency: Optional[str]
    totalAmountDescription: Optional[str]


class AddtionalInfoItem(SimplenightModel):
    message: str


class AdditionalInfo(SimplenightModel):
    notice: Optional[str]
    garageToGarageEstimate: Optional[str]
    additionalInfo: Optional[List[AddtionalInfoItem]]


class QuoteResponse(SimplenightModel):
    pickUpDate: str
    pickUpLoacation: Location
    dropOffLocation: Location
    flightInfo: Optional[FlightInfo]
    vehicleDetails: VehicleDetails
    chargeDetails: ChargeDetails
    chargeItems: List[ChargeItem]
    reference: Reference
    total: TotalAmount
    additional: AdditionalInfo
    special: Optional[str]
    tripType: str = "Point-To-Point"
    passengers: int
    bags: int


class PassengerInfo(SimplenightModel):
    firstName: str
    lastName: str
    phoneNum: str


class PaymentInfo(SimplenightModel):
    cardType: str
    cardNum: str
    cardName: str
    expCVV: str
    expDate: str
    billingAddress: Location


class BookReservationRequest(SimplenightModel):
    passengerInfo: PassengerInfo
    paymentInfo: PaymentInfo
    quoteInfo: QuoteResponse


class FindReservationRequest(SimplenightModel):
    reservation_id: str
    lastname: str
