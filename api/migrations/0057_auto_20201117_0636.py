# Generated by Django 3.1.2 on 2020-11-17 06:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0056_auto_20201116_1957"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organizationfeatures",
            name="name",
            field=models.TextField(
                choices=[
                    ("enabled_connectors", "ENABLED_ADAPTERS"),
                    ("test_mode", "TEST_MODE"),
                    ("stripe_api_key", "STRIPE_API_KEY"),
                    ("priceline_api_url", "PRICELINE_API_URL"),
                    ("mailgun_api_key", "MAILGUN_API_KEY"),
                    ("email_enabled", "EMAIL_ENABLED"),
                ]
            ),
        ),
    ]
