from rest_framework import serializers
from api.models import models

import json

from django.contrib.auth.models import User

# from django.core.files.uploadedfile import InMemoryUploadedFile

# Venue Serializer


def is_json(text: str) -> bool:
    from json import loads, JSONDecodeError

    if not isinstance(text, (str, bytes, bytearray)):
        return False
    if not text:
        return False
    text = text.strip()
    if text:
        if text[0] in {"{", "["} and text[-1] in {"}", "]"}:
            try:
                loads(text)
            except (ValueError, TypeError, JSONDecodeError):
                return False
            else:
                return True
        else:
            return False
    return False


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "username", "is_staff", "is_superuser", "is_active")


class VenueMediaSerializer(serializers.ModelSerializer):
    # def __init__(self, *args, **kwargs):
    #     file_fields = kwargs.pop('file_fields', None)
    #     super().__init__(*args, **kwargs)
    #     if file_fields:
    #         field_update_dict = {field: serializers.FileField
    # (required=False, write_only=True) for field in file_fields}
    #         self.fields.update(**field_update_dict)

    # def create(self, validated_data):
    #     validated_data_copy = validated_data.copy()
    #     validated_files = []
    #     for key, value in validated_data_copy.items():
    #         if isinstance(value, InMemoryUploadedFile):
    #             validated_files.append(value)
    #             validated_data.pop(key)
    #     submission_instance = super().create(validated_data)
    #     for file in validated_files:
    #         models.VenueMedia.objects.create(submission=submission_instance, file=file)
    #     return submission_instance

    class Meta:
        model = models.VenueMedia
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(VenueMediaSerializer, self).to_representation(instance)
        rep["venue_id"] = instance.venue.id
        del rep["venue"]
        return rep


class VenueCreateMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenueMedia
        fields = "__all__"


class VenueContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenueContact
        fields = "__all__"


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PaymentMethod
        fields = "__all__"


class VenueDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.VenueDetail
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(VenueDetailSerializer, self).to_representation(instance)
        if is_json(rep["payment_method"]):
            rep["payment_method"] = json.loads(rep["payment_method"])
        if is_json(rep["availability"]):
            rep["availability"] = json.loads(rep["availability"])
        if is_json(rep["holidays"]):
            rep["holidays"] = json.loads(rep["holidays"])
        if is_json(rep["amenities"]):
            rep["amenities"] = json.loads(rep["amenities"])
        return rep

    def update(self, instance, validated_data):
        for update in validated_data:
            setattr(instance, update, validated_data[update])
        if "payment_method" not in validated_data:
            instance.payment_method = json.loads(instance.payment_method)
        if "availability" not in validated_data:
            instance.availability = json.loads(instance.availability)
        if "holidays" not in validated_data:
            instance.holidays = json.loads(instance.holidays)
        if "amenities" not in validated_data:
            instance.amenities = json.loads(instance.amenities)
        instance.save()
        return instance


class ProductGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductGroup
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(ProductGroupSerializer, self).to_representation(instance)
        rep["venue_id"] = instance.venue.id
        del rep["venue"]
        return rep


class ProductNightLifeMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductsNightLifeMedia
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(ProductNightLifeMediaSerializer, self).to_representation(instance)
        rep["venue_id"] = instance.venue.id
        del rep["venue"]
        return rep


class ProductHotelsMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductHotelsMedia
        fields = "__all__"


class ProductsNightLifeSerializer(serializers.ModelSerializer):
    media = ProductNightLifeMediaSerializer(many=True, read_only=True)
    group = serializers.SerializerMethodField(source="get_group")

    class Meta:
        model = models.ProductsNightLife
        fields = "__all__"

    def get_group(self, obj):
        return obj.name

    def to_representation(self, instance):
        rep = super(ProductsNightLifeSerializer, self).to_representation(instance)
        rep["venue_id"] = instance.venue.id
        del rep["venue"]
        return rep


class VenueSerializer(serializers.ModelSerializer):
    media = VenueMediaSerializer(many=True, read_only=True)
    details = VenueDetailSerializer(many=True, read_only=True)
    contacts = VenueContactSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    products = ProductsNightLifeSerializer(many=True, read_only=True)

    class Meta:
        model = models.Venue
        fields = "__all__"


class ProductsHotelRoomDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductsHotelRoomDetails
        fields = "__all__"


class ProductsHotelRoomPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductsHotelRoomPricing
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(ProductsHotelRoomPricingSerializer, self).to_representation(instance)
        if is_json(rep["rate"]):
            rep["rate"] = json.loads(rep["rate"])
        if is_json(rep["taxes"]):
            rep["taxes"] = json.loads(rep["taxes"])
        if is_json(rep["guests"]):
            rep["guests"] = json.loads(rep["guests"])
        if is_json(rep["dates"]):
            rep["dates"] = json.loads(rep["dates"])
        return rep

    def update(self, instance, validated_data):
        for update in validated_data:
            setattr(instance, update, validated_data[update])
        if "rate" not in validated_data:
            instance.rate = json.loads(instance.rate)
        if "taxes" not in validated_data:
            instance.taxes = json.loads(instance.taxes)
        if "guests" not in validated_data:
            instance.guests = json.loads(instance.guests)
        if "dates" not in validated_data:
            instance.dates = json.loads(instance.dates)
        instance.save()
        return instance


class ProductHotelSerializer(serializers.ModelSerializer):
    media = ProductHotelsMediaSerializer(many=True, read_only=True)
    hotels_room_details = ProductsHotelRoomDetailsSerializer(many=True, read_only=True)
    hotels_room_pricing = ProductsHotelRoomPricingSerializer(many=True, read_only=True)

    class Meta:
        model = models.ProductHotel
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(ProductHotelSerializer, self).to_representation(instance)
        rep["venue_id"] = instance.venue.id
        if is_json(rep["room_details"]):
            rep["room_details"] = json.loads(rep["room_details"])
        del rep["venue"]
        return rep

    def update(self, instance, validated_data):
        for update in validated_data:
            setattr(instance, update, validated_data[update])
        if "room_details" not in validated_data:
            instance.room_details = json.loads(instance.room_details)
        instance.save()
        return instance
