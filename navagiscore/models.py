# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.gis.db import models

# Create your models here.
class clients(models.Model):
	organization = models.CharField(max_length=50, default=u'')
	clientid = models.CharField(max_length=50, default=u'')
	password = models.CharField(max_length=50, default=u'')
	registration = models.CharField(max_length=50, default=u'')
	expiry = models.CharField(max_length=50, default=u'')

class shapefiles(models.Model):
	name = models.CharField(max_length=100, default=u'')
	uploaded_date = models.CharField(max_length=50, default=u'')
	uploaded_time = models.CharField(max_length=50, default=u'')
	status = models.CharField(max_length=50, default=u'processing')
	download_link = models.CharField(max_length=1000, default=u'')
