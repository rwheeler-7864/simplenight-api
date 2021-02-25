from django.contrib import admin
from django.urls import path, include

import api.view.admin_view
import api.view.hotels_view
import api.view.locations
import api.view.default_view
import api.view.charging_view
import api.view.urban_view
import api.view.carey_view
import api.view.dinings_view
import api.accounts.views
import api.view.multi_product_views
from api.view import venue_view
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_extensions.routers import ExtendedSimpleRouter
from rest_framework.schemas import get_schema_view

router = ExtendedSimpleRouter(trailing_slash=False)


router.register(r"locations", api.view.locations.LocationsViewSet, basename="locations")
router.register(r"hotels", api.view.hotels_view.HotelViewSet, basename="hotels")
router.register(r"multi", api.view.multi_product_views.AllProductsViewSet, basename="multi")
router.register(r"charging", api.view.charging_view.ChargingViewSet, basename="charging")
router.register(r"urban", api.view.urban_view.UrbanViewSet, basename="urban")
router.register(r"carey", api.view.carey_view.CareyViewSet, basename="carey")
router.register(r"dinings", api.view.dinings_view.DiningViewSet, basename="dinings")
router.register(r"authentication", api.view.default_view.AuthenticationView, basename="authentication")
router.register(r"users", api.view.admin_view.UserViewSet, basename="user-list")
router.register(r"payment-methods", venue_view.PaymentMethodViewSet, basename="payment-methods-list")
router.register(r"venues", venue_view.VenueViewSet).register(
    r"media", venue_view.VenueMediaViewSet, "venue_id", parents_query_lookups=["venue_id"]
)
router.register(r"venues", venue_view.VenueViewSet).register(
    r"contact", venue_view.VenueContactViewSet, "venue_id", parents_query_lookups=["venue_id"]
)
router.register(r"venues", venue_view.VenueViewSet).register(
    r"details", venue_view.VenueDetailViewSet, "venue_id", parents_query_lookups=["venue_id"]
)
router.register(r"venues", venue_view.VenueViewSet).register(
    r"product-group", venue_view.ProductGroupViewSet, "venue_id", parents_query_lookups=["venue_id"]
)
(
    router.register(r"venues", venue_view.VenueViewSet).register(
        r"product_nightlife", venue_view.ProductNightLifeViewSet, "venue_id", parents_query_lookups=["venue_id"]
    )
)
(
    router.register(r"venues", venue_view.VenueViewSet).register(
        r"product_hotels", venue_view.ProductHotelViewSet, "venue_id", parents_query_lookups=["venue_id"]
    )
)
router.register(r"hotel_room_details", venue_view.ProductsHotelRoomDetailsViewSet, basename="hotel-room-details-list")

router.register(
    r"hotel_room_pricing", venue_view.ProductsHotelRoomPricingDetailsViewSet, basename="hotel-room-details-list"
)

router.register(r"product_hotels_media", venue_view.ProductHotelMediaViewSet, basename="product-hotels-media-list")
router.register(
    r"product_nightlife_media", venue_view.ProductNightLifeMediaViewSet, basename="product-hotels-media-list"
)

router.urls.append(path("accounts/", include("api.accounts.urls")))

urlpatterns = [
    path("", api.view.default_view.index),
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path(
        "openapi",
        get_schema_view(title="Simplenight Hotel API", description="Test data", version="1.0.0"),
        name="openapi-schema",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
