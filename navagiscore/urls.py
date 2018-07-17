#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
	url('^$', views.index, name='index'),
	url('^cluster/$',views.cluster, name='cluster'),
	url('^login/$',views.login, name='login'),
	url('^getshapefiles/$',views.getshapefiles, name='getshapefiles'),
	url('^shapefilename/$',views.shapefilename, name='shapefilename'),
	url('^uploadzipshapefile/$',views.uploadzipshapefile, name='uploadzipshapefile'),
	url('^webgl/$',views.webgl, name='webgl')
]
