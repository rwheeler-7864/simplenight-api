# Generated by Django 3.1.2 on 2021-01-20 17:30

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_auto_20210120_1704'),
    ]

    operations = [
        migrations.CreateModel(
            name='VenueContacts',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('MAIN', 'MAIN'), ('OTHER', 'OTHER')], default='MAIN', max_length=5)),
                ('website', models.TextField(blank=True, null=True)),
                ('phone_number', models.TextField(blank=True, null=True)),
                ('fax', models.TextField(blank=True, null=True)),
                ('email', models.TextField(blank=True, null=True)),
                ('title', models.TextField(blank=True, null=True)),
                ('department', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('venue_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.venue')),
            ],
            options={
                'verbose_name': 'VenueContact',
                'verbose_name_plural': 'VenueContacts',
                'db_table': 'venue_contacts',
            },
        ),
    ]