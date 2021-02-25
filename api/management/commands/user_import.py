#!/usr/bin/env python

import json

from api import logger
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

    def handle(self, *args, **options):
        logger.info("Import user data start")
        f = open(settings.BASE_DIR+'/api/resources/users/user_data.json')
        data = json.load(f) 
        print(data['users'])
        for user in data['users']:
            try:
                user_obj = User(
                    email   = user['email'],
                    username = user['username'],
                    is_staff = user['is_staff'],
                    is_superuser = user['is_superuser'],
                    is_active = user['is_active'],
                )
                user_obj.set_password(user['password'])
                user_obj.save()
            except Exception as e:
                logger.error("User already exists {}".format(e))


        logger.info("Import user data End")