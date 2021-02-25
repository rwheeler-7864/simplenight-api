import requests
from lxml import etree

from api.urban.constants import CONFIG

class UrbanService:
    def __init__(self, env="development"):
        self.config = CONFIG
        self.username = self.config[env]["username"]
        self.password = self.config[env]["password"]
        self.url = self.config[env]["end_point"]

    def get_access_body(self, params={}, currency=''):
        data = etree.Element('data')
        data.set('type', 'clsGetUACountryListRQ')
        access = etree.Element('Access')
        access.set('type', 'clsAccessType')
        data.append(access)
        username = etree.Element('UserName')
        username.text = self.username
        password = etree.Element('Password')
        password.text = self.password
        access.append(username)
        access.append(password)
        _currency = etree.Element('Currency')
        _currency.text = currency
        access.append(_currency)
        for param in params:
            if type(params[param]) is dict:
                new_root = etree.Element(param)
                if param == 'Traveller':
                    new_root.set('type', 'clsTravellerInfo')
                elif param == 'Other':
                    new_root.set('type', 'clsTravellerOther')
                for new_param in params[param]:
                    new_root_node = etree.Element(new_param)
                    new_root_node.text = params[param][new_param]
                    new_root.append(new_root_node)
                data.append(new_root)
            else:
                new_node = etree.Element(param)
                new_node.text = params[param]
                data.append(new_node)
        return etree.tostring(data)

    def get_standard_countries(self, request):
        _url = self.url + "get_standard_countries"
        response = requests.post(_url, data=self.get_access_body())
        return response

    def get_ua_countries(self, request):
        _url = self.url + "get_ua_countries"
        response = requests.post(_url, data=self.get_access_body())
        return response

    def get_ua_destinations(self, request):
        _url = self.url + "get_ua_destinations"
        params = {}
        if request.GET.get('ua_country_id'):
            params['UACountryID'] = request.GET.get('ua_country_id')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_trips(self, request):
        _url = self.url + "get_trips"
        params = {}
        currency = ''
        if request.GET.get('ua_country_id'):
            params['UACountryID'] = request.GET.get('ua_country_id')
        if request.GET.get('ua_destination_id'):
            params['UADestinationID'] = request.GET.get('ua_destination_id')
        if request.GET.get('departure_from'):
            params['DepartureFrom'] = request.GET.get('departure_from')
        if request.GET.get('departure_to'):
            params['DepartureTo'] = request.GET.get('departure_to')
        if request.GET.get('currency'):
            currency = request.GET.get('currency')
        response = requests.post(_url, data=self.get_access_body(params, currency))
        return response

    def get_trip_info(self, request):
        _url = self.url + "get_trip_info"
        params = {}
        if request.GET.get('trip_code'):
            params['TripCode'] = request.GET.get('trip_code')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_trip_alm(self, request):
        _url = self.url + "get_trip_alm"
        params = {}
        if request.GET.get('trip_code'):
            params['TripCode'] = request.GET.get('trip_code')
        if request.GET.get('dep_date'):
            params['DepDate'] = request.GET.get('dep_date')
        if request.GET.get('dep_id'):
            params['DepId'] = request.GET.get('dep_id')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_trip_price(self, request):
        _url = self.url + "get_trip_price"
        params = {}
        if request.GET.get('trip_code'):
            params['TripCode'] = request.GET.get('trip_code')
        if request.GET.get('dep_date'):
            params['DepDate'] = request.GET.get('dep_date')
        if request.GET.get('dep_id'):
            params['DepId'] = request.GET.get('dep_id')
        if request.GET.get('num_adult'):
            params['NumAdult'] = request.GET.get('num_adult')
        if request.GET.get('num_adult'):
            params['NumChild'] = request.GET.get('num_child')
        if request.GET.get('promo_code'):
            params['PromoCode'] = request.GET.get('promo_code')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_trip_avail_date(self, request):
        _url = self.url + "get_trip_avail_date"
        params = {}
        if request.GET.get('trip_code'):
            params['TripCode'] = request.GET.get('trip_code')
        if request.GET.get('start_date'):
            params['StartDate'] = request.GET.get('start_date')
        if request.GET.get('end_date'):
            params['EndDate'] = request.GET.get('end_date')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_trip_availabilities(self, request):
        _url = self.url + "get_trip_availabilities"
        params = {}
        if request.GET.get('trip_code'):
            params['TripCode'] = request.GET.get('trip_code')
        if request.GET.get('start_date'):
            params['StartDate'] = request.GET.get('start_date')
        if request.GET.get('end_date'):
            params['EndDate'] = request.GET.get('end_date')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def book_trip(self, request):
        _url = self.url + "book_trip"
        params = {
            'Traveller': {},
            'Other': {}
        }
        if request.GET.get('trip_code'):
            params['TripCode'] = request.GET.get('trip_code')
        if request.GET.get('dep_date'):
            params['DepDate'] = request.GET.get('dep_date')
        if request.GET.get('dep_id'):
            params['DepId'] = request.GET.get('dep_id')
        if request.GET.get('num_adult'):
            params['NumAdult'] = request.GET.get('num_adult')
        if request.GET.get('num_adult'):
            params['NumChild'] = request.GET.get('num_child')
        if request.GET.get('promo_code'):
            params['PromoCode'] = request.GET.get('promo_code')
        if request.GET.get('gift_cert'):
            params['GiftCert'] = request.GET.get('gift_cert')
        if request.GET.get('salutation'):
            params['Traveller']['Salutation'] = request.GET.get('salutation')
        if request.GET.get('first_name'):
            params['Traveller']['FirstName'] = request.GET.get('first_name')
        if request.GET.get('last_name'):
            params['Traveller']['LastName'] = request.GET.get('last_name')
        if request.GET.get('dob'):
            params['Traveller']['DOB'] = request.GET.get('dob')
        if request.GET.get('standard_country_id'):
            params['Traveller']['StandardCountryID'] = request.GET.get('standard_country_id')
        if request.GET.get('phone'):
            params['Traveller']['Phone'] = request.GET.get('phone')
        if request.GET.get('mobile'):
            params['Traveller']['Mobile'] = request.GET.get('mobile')
        if request.GET.get('email'):
            params['Traveller']['Email'] = request.GET.get('email')
        if request.GET.get('password'):
            params['Traveller']['Password'] = request.GET.get('password')
        if request.GET.get('other_salutation'):
            params['Other']['Salutation'] = request.GET.get('other_salutation')
        if request.GET.get('other_first_name'):
            params['Other']['FirstName'] = request.GET.get('other_first_name')
        if request.GET.get('other_last_name'):
            params['Other']['LastName'] = request.GET.get('other_last_name')
        if request.GET.get('other_dob'):
            params['Other']['DOB'] = request.GET.get('other_dob')
        if request.GET.get('is_adult'):
            params['Other']['IsAdult'] = request.GET.get('is_adult')
        if request.GET.get('hotel_location'):
            params['HotelLocation'] = request.GET.get('hotel_location')
        if request.GET.get('request'):
            params['Request'] = request.GET.get('request')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def cancel_booking(self, request):
        _url = self.url + "cancel_booking"
        params = {}
        if request.GET.get('ref_no'):
            params['RefNo'] = request.GET.get('ref_no')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_booking_voucher(self, request):
        _url = self.url + "get_booking_voucher"
        params = {}
        if request.GET.get('ref_no'):
            params['RefNo'] = request.GET.get('ref_no')
        response = requests.post(_url, data=self.get_access_body(params))
        return response
    
    def get_booking_info(self, request):
        _url = self.url + "get_booking_info"
        params = {}
        if request.GET.get('ref_no'):
            params['RecordLocator'] = request.GET.get('ref_no')
        response = requests.post(_url, data=self.get_access_body(params))
        return response

    def get_exchange_rate_list(self, request):
        _url = self.url + "get_exchange_rate_list"
        response = requests.post(_url, data=self.get_access_body())
        return response
