# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-14 22:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('navagiscore', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clients',
            name='org_id',
        ),
        migrations.AddField(
            model_name='clients',
            name='organization',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='clients',
            name='clientid',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='clients',
            name='password',
            field=models.CharField(default='', max_length=50),
        ),
    ]
