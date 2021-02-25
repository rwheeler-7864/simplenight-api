from api.hotel.models.hotel_api_model import SimplenightAmenities


HOTELBEDS_AMENITY_MAPPINGS = {
    SimplenightAmenities.POOL: ["306", "313", "326", "360", "361", "362", "363", "364", "365", "573", "615"],
    SimplenightAmenities.FREE_PARKING: [],
    SimplenightAmenities.PARKING: ["500", "560"],
    SimplenightAmenities.BREAKFAST: ["11", "12", "160", "170", "180", "200", "264", "30", "35", "360", "40", "580"],
    SimplenightAmenities.WIFI: ["261", "550"],
    SimplenightAmenities.AIRPORT_SHUTTLE: ["562"],
    SimplenightAmenities.KITCHEN: ["110", "115"],
    SimplenightAmenities.PET_FRIENDLY: ["535", "540"],
    SimplenightAmenities.AIR_CONDITIONING: ["10", "170", "180", "575"],
    SimplenightAmenities.CASINO: ["180"],
    SimplenightAmenities.WATER_PARK: ["610"],
    SimplenightAmenities.ALL_INCLUSIVE: ["257", "258", "259", "260", "263"],
    SimplenightAmenities.SPA: ["460", "620"],
    SimplenightAmenities.WASHER_DRYER: ["145", "321", "568"],
    SimplenightAmenities.LAUNDRY_SERVICES: ["280"],
    SimplenightAmenities.HOT_TUB: ["305", "410"],
    SimplenightAmenities.BAR: ["555", "570", "130", "590"],
    SimplenightAmenities.MINIBAR: ["120"],
    SimplenightAmenities.GYM: ["470", "308", "295"],
    SimplenightAmenities.RESTAURANT: ["200"],
    SimplenightAmenities.SAUNA: ["307", "420"],
}


def get_simplenight_amenity_mappings(amenity_codes):
    amenity_mappings = []
    if not amenity_codes or len(amenity_codes) == 0:
        return amenity_codes
    for amenity, codes in HOTELBEDS_AMENITY_MAPPINGS.items():
        if any(x for x in amenity_codes if x in codes):
            amenity_mappings.append(amenity)

    return amenity_mappings
