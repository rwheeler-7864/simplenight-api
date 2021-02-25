from enum import Enum
from api.hotel.models.hotel_api_model import ImageType


HOTELBEDS_LANGUAGE_MAP = {
    "en": "ENG",
    "ca": "CAT",
    "da": "DAN",
    "de": "ALE",
    "es": "CAS",
    "fr": "FRA",
    "hu": "HUN",
    "id": "IND",
    "it": "ITA",
    "ja": "JPN",
    "ms": "MAL",
    "nl": "HOL",
    "no": "NOR",
    "pl": "POL",
    "sv": "SUE",
    "th": "TAI",
    "zh": "CHI"
}


def get_language_mapping(language):
    return HOTELBEDS_LANGUAGE_MAP.get(language, "ENG")


IMAGE_URL_PREFIX = "//photos.hotelbeds.com/giata"
"""
    format: http://photos.hotelbeds.com/giata/{size}/{path}
    e.g.  : http://photos.hotelbeds.com/giata/00/000001/000001a_hb_a_001.jpg
    size  :
        None     320    standard
        small    74     thumbnail
        medium   117
        bigger   800
        xl       1024
        xxl      2048
        original (vary)
"""


def get_thumbnail_url(images):
    if len(images) == 0:
        return
    filtered_images = [x for x in images if x["imageTypeCode"] == "GEN"]
    if len(filtered_images) == 0:
        filtered_images = images
    ordered = sorted(filtered_images, key=lambda x: x["order"])
    image_path = ordered[0]["path"]
    return f"{IMAGE_URL_PREFIX}/{image_path}"


def get_image_url(image_path, size="bigger"):
    return f"{IMAGE_URL_PREFIX}/{size}/{image_path}"


IMAGE_TYPE_MAP = {
    "HAB": ImageType.ROOM
}


def get_image_type(image_type_code):
    return IMAGE_TYPE_MAP.get(image_type_code, ImageType.UNKNOWN)


HOTELBEDS_STAR_RATING_MAP = {
    "1EST": 1,
    "1LL": 1,
    "2EST": 2,
    "2LL": 2,
    "3EST": 3,
    "3LL": 3,
    "4EST": 4,
    "4LL": 4,
    "4LUX": 4,
    "5EST": 5,
    "5LL": 5,
    "5LUX": 5,
    "AG": 4,
    "ALBER": 1,
    "APTH": 1,
    "APTH2": 2,
    "APTH3": 3,
    "APTH4": 4,
    "APTH5": 5,
    "AT1": 4,
    "AT2": 3,
    "AT3": 2,
    "BB": 3,
    "BB3": 3,
    "BB4": 4,
    "BB5": 5,
    "BOU": 4,
    "CAMP1": 1,
    "CAMP2": 2,
    "CHUES": 2,
    "H1_5": 1.5,
    "H2S": 2,
    "H2_5": 2.5,
    "H3S": 3,
    "H3_5": 3.5,
    "H4_5": 4.5,
    "H5_5": 5.5,
    "HIST": 5,
    "HR": 3,
    "HR2": 2,
    "HR3": 3,
    "HR4": 4,
    "HR5": 5,
    "HRS": 4,
    "HS": 1,
    "HS2": 2,
    "HS3": 3,
    "HS4": 4,
    "HS5": 5,
    "HSR1": 1,
    "HSR2": 2,
    "LODGE": 2,
    "MINI": 2,
    "PENDI": 0,
    "PENSI": 1,
    "POUSA": 4,
    "RESID": 3,
    "RSORT": 4,
    "SPC": 3,
    "STD": 2,
    "SUP": 4,
    "VILLA": 4,
    "VTV": 4,
}


def get_star_rating(category_code):
    return HOTELBEDS_STAR_RATING_MAP.get(category_code, None)


def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct
