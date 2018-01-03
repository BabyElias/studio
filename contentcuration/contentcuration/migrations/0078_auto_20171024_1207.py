# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-10-24 19:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contentcuration', '0077_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='included_languages',
            field=models.ManyToManyField(blank=True, related_name='channels', to='contentcuration.Language', verbose_name='languages'),
        ),
        migrations.AddField(
            model_name='channel',
            name='published_kind_count',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='channel',
            name='published_size',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='channel',
            name='total_resource_count',
            field=models.IntegerField(default=0),
        ),
    ]