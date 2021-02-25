from django import forms
from django.contrib import admin
from django.forms import TextInput

from api.models.models import (
    Booking,
    OrganizationFeatures,
    PropertyInfo,
    Venue,
    VenueMedia,
    VenueContact,
    VenueDetail,
    PaymentMethod,
    # ProductMedia,
    ProductHotelsMedia,
    ProductsNightLifeMedia,
    ProductGroup,
    ProductsNightLife,
    ProductHotel,
    ProductsHotelRoomDetails,
    ProductsHotelRoomPricing,
)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_per_page = 100


@admin.register(OrganizationFeatures)
class OrganizationFeatureInline(admin.ModelAdmin):
    class Form(forms.ModelForm):
        class Meta:
            model = OrganizationFeatures
            fields = "__all__"
            widgets = {
                "value": TextInput(attrs={"size": 60}),
            }

    form = Form
    list_display = ("organization_name", "name", "value")
    list_filter = ("organization__name",)
    widgets = {
        "value": TextInput(attrs={"size": 20}),
    }


@admin.register(PropertyInfo)
class PropertyInfoAdmin(admin.ModelAdmin):
    list_display = ("provider", "provider_code", "type", "language_code", "description")
    list_filter = ("provider_code", "language_code")


admin.site.register(Venue)
admin.site.register(VenueMedia)
admin.site.register(VenueContact)
admin.site.register(VenueDetail)
admin.site.register(PaymentMethod)
admin.site.register(ProductHotelsMedia)
admin.site.register(ProductsNightLifeMedia)

admin.site.register(ProductHotel)

admin.site.register(ProductGroup)
admin.site.register(ProductsNightLife)
admin.site.register(ProductsHotelRoomDetails)
admin.site.register(ProductsHotelRoomPricing)
