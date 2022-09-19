# Generated by Django 3.2.5 on 2022-05-26 22:00
import django.db.models.deletion
import rest_framework.utils.encoders
from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('sessions', '0001_initial'),
        ('contentcuration', '0137_channelhistory'),
    ]

    operations = [
        migrations.CreateModel(
            name='Change',
            fields=[
                ('server_rev', models.BigAutoField(primary_key=True, serialize=False)),
                ('client_rev', models.IntegerField(blank=True, null=True)),
                ('table', models.CharField(max_length=32)),
                ('change_type', models.IntegerField()),
                ('kwargs', models.JSONField(encoder=rest_framework.utils.encoders.JSONEncoder)),
                ('applied', models.BooleanField(default=False)),
                ('errored', models.BooleanField(default=False)),
                ('channel', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contentcuration.channel')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='changes_by_user', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sessions.session')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='changes_about_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
