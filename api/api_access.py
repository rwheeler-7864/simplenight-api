from api import logger
from api.auth.authentication import OrganizationAPIKey
from api.models.models import Organization
from api.common.common_models import SimplenightModel


class ApiAccessRequest(SimplenightModel):
    name: str


class ApiAccessResponse(SimplenightModel):
    api_key: str
    key: str


def create_anonymous_api_user(request: ApiAccessRequest):
    logger.info(f"Creating API Key for user {request.name}")

    anonymous_org = Organization.objects.get(name="anonymous")
    api_key, key = OrganizationAPIKey.objects.create_key(name=request.name, organization=anonymous_org)

    return ApiAccessResponse(api_key=api_key, key=key)
