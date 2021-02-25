import json

import requests

from api import logger
from api.common import request_context


def get_api_key():
    # return "api", "4fc764e45639a2008a075f69a0706591-2fbe671d-1bc16189"
    return "api", "key - bac028e7dd9f2fe6c438e9189c62b537"


def get_api_host():
    if not request_context.get_test_mode():
        return "https://api.mailgun.net/v3/mg.simplenight.com/messages"
    else:
        return "https://api.mailgun.net/v3/sandbox4d76d5beb24f4ba790d3ccf7cda332c4.mailgun.org/messages"


def send_mail(template_name, subject, name, to_email, variables=None):
    if not variables:
        variables = {}

    params = {
        "from": "SIMPLENIGHT® <no-reply@simplenight.com>",
        "to": f"{name} <{to_email}>",
        "subject": subject,
        "template": template_name,
        "h:X-Mailgun-Variables": json.dumps(variables)
    }

    logger.info(f"Sending email for template {template_name} {subject} with variables {variables}")
    response = requests.post(get_api_host(), auth=get_api_key(), data=params)
    logger.info(response.text)
