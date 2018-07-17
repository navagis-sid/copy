# -*- coding: utf-8 -*-
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import HttpResponse
from django.shortcuts import render

import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint
from math import sin, cos, sqrt, atan2, radians
import io, os, json, sys, copy, hashlib
from django.views.decorators.csrf import csrf_exempt

import datetime
import requests
import hashlib
from requests.auth import AuthBase, HTTPBasicAuth
from navagiscore.models import *
import os
from django.views.decorators.csrf import ensure_csrf_cookie
import zipfile

#host = "https://ec2-52-221-219-74.ap-southeast-1.compute.amazonaws.com:443/"
host = "http://10.25.51.11:8000/"
token = 'c1256939dae6c3f95949481304ec67ccc2a96143'
ver = False

class TokenAuthenticator(AuthBase):

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Token ' + str(self.token)
        return r

@ensure_csrf_cookie
def index(request):
	template_name = 'index.html'
	context = {'app_name': 'geocore','messageerror': '','groupname': 'Geocore-Cobena'}
	if request.method == 'POST':
		try:
			if 'logout' in request.POST:
				request.session.flush()
				template_name = 'user_login.html'
			else:
				in_user = request.POST['username']
				in_pass = request.POST['password']
				print in_user
				print in_pass
				password = hashlib.md5(in_pass).hexdigest()
				client = clients.objects.filter(clientid=in_user, password=password).values('expiry')[::1]
				if len(client) == 0:
					template_name = 'user_login.html'
					context['messageerror'] = 'Wrong username and password.'
					return render(request, template_name, context)
				try:
					result = check_account(in_user)
					if result:
						template_name = 'user_login.html'
						context['messageerror'] = 'Expired Account'
						return render(request, template_name, context)
				except:
					context['messageerror'] = 'User doesn\'t Exist'
					print 'User does not exist'
				request.session['username'] = in_user
		except:
			for key in request.session.keys():
				if key == 'username':
					continue
				del request.session[key]
			template_name = 'user_login.html'
			print ('Unexpected error:', sys.exc_info()[0])

	elif request.method == 'GET' and 'username' in request.session:
		for key in request.session.keys():
			if key == 'username':
				continue
			del request.session[key]
		print 'index GET request loggedin alreadys'
	else:
		template_name = 'user_login.html'
		print 'not logged in'
	print template_name
	return render(request, template_name, context)

def get_poi(subcat_id_list, level_id, place_id, cat_level, host, token):
	response = {}
	try:
		url = host + 'get_poi/' + str(subcat_id_list) + '/' + level_id + '/' + str(place_id) + '/' + str(cat_level) + '/'
		print url
		r = requests.get(url, auth=TokenAuthenticator(token), verify=ver)
		response = r.json()
	except requests.exceptions.ConnectionError as e:
		print e
	except TypeError as e:
		print e
	except:
		print ('get_poi error:', sys.exc_info()[0])

	return response

def check_account(client_id):
	result = {'status': 'failed', 'message': 'Client ID doesn\'t exist. Please contact NAVAGIS Sales Representative. www.navagis.com' }
	client = clients.objects.filter(clientid=client_id).values('expiry')[::1]
	if len(client) == 0:
		return result
	else:				
		result = {'status': 'failed', 'message': 'Expired account. Please contact NAVAGIS Sales Representative. www.navagis.com'}
		expiry = client[0]['expiry'].split('/')
		d = datetime.date.today()
		print str(int(expiry[2]) > int(d.year))
		print str(int(expiry[2]) == int(d.year) and int(expiry[0]) > int(d.month))
		print str(int(expiry[2]) == int(d.year) and int(expiry[0]) == int(d.month) and int(expiry[1]) >= int(d.day))

		if not (int(expiry[2]) > int(d.year) 
			or (int(expiry[2]) == int(d.year) and int(expiry[0]) > int(d.month)) or (int(expiry[2]) == int(d.year) and int(expiry[0]) == int(d.month) and int(expiry[1]) >= int(d.day))):
			return result
	result = {}
	return result

@api_view(['GET'])
def login(request):
	if request.method == 'GET':
		result = {}
		try:
			print 'Login'
			client_id = request.GET.get('client_id', '')

			result = check_account(client_id)
			if result:
				return Response(result) 
			result = {'status': 'success', 'message': 'Thank you for using NAVAGIS services. www.navagis.com' }
		except NameError as e:
			print e
		except:
			print ('client_login error:', sys.exc_info()[0])
		return Response(result)

@api_view(['GET'])
def cluster(request):
	if request.method == 'GET':
		result = {}
		try:
			print 'Cluster Points Cobena'

			client_id = request.GET.get('client_id', '')
			subcat_id_list = request.GET.get('subcat_id_list', '')
			level_id = request.GET.get('level_id', '')
			place_id = request.GET.get('place_id', '')
			host = request.GET.get('host','') 
			print host
			cat_level = 'sub_category'
			subcat_id_list = (str(subcat_id_list)).replace(",", "&")

			if not os.path.exists('static/cluster/'):
				os.makedirs('static/cluster/')

			name = subcat_id_list + cat_level + str(place_id) + str(level_id)
			name_md5 = hashlib.md5(name).hexdigest()
			filename = 'static/cluster/' + name_md5 + '.txt'

			result = check_account(client_id)
			if result:
				return Response(result) 
			points = []

			if os.path.isfile(filename):
				with open(filename) as json_data:
					result = json.load(json_data)
				json_data.close()
				return Response(result)

			radius = 1
			poi_list = get_poi(subcat_id_list, level_id, place_id, cat_level, host, token)
			for subcat_id in poi_list:
				points = points + poi_list[subcat_id]

			print "Unclustered Points Length: " + str(subcat_id_list) + " - " + str(len(points))
			clustered_pois = json.loads(dbscan_cluster_pois(points,radius))
			
			print "Initial Clustering Length: " + str(subcat_id_list) + " - " + str(len(clustered_pois))
			result = cluster_navagis(clustered_pois)
			with open(filename, 'wb') as f:
				json.dump(result, f)
			f.close()
			print host
		except NameError as e:
			print e
		except:
			print ('cluster error:', sys.exc_info()[0])
		return Response(result)

@api_view(['POST'])
def shapefilename(request):
	if request.method == 'POST':
		temp_a = {'status': 'failure'}
		try:
			post_data = json.loads(request.body)
			filename = post_data['filename']
			request.session['filename'] = filename
			temp_a = {'status': 'success'}
		except UnboundLocalError as e:
			print e
		except:
			print ('shapefilename error:', sys.exc_info()[0])
		return Response(temp_a)

@api_view(['POST'])
def getshapefiles(request):
	if request.method == 'POST':
		result = {'status': 'failure'}
		try:
			shapefile_list = shapefiles.objects.values('id', 'name', 'uploaded_date', 'uploaded_time', 'status', 'download_link')[::1]
			result['status'] = 'success'
			for sh in shapefile_list:
				sh['is_done'] = False
				if sh['download_link'] != '':
					sh['is_done'] = True
			result['shapefiles'] = shapefile_list
			print shapefile_list
		except UnboundLocalError as e:
			print e
		except:
			print ('shapefilename error:', sys.exc_info()[0])
		return Response(result)

@api_view(['POST'])
def uploadzipshapefile(request):
	if request.method == 'POST':
		temp_a = {'status': 'failure'}
		try:
			date = datetime.datetime.now().strftime('%d %b %Y').upper()
			time = datetime.datetime.now().strftime('%I:%M %p').upper()
			data = request.stream.read()
			print 'uploadzipshapefile'
			name = 'shapefile' + "_" + date.replace(' ', '_') + "_" + time.replace(' ', '_')
			if 'filename' in request.session:
				name = request.session['filename'] + date.replace(' ', '_') + "_" + time.replace(' ', '_')
			filename = 'static/shapefiles/' + name + '.zip'

			if not os.path.exists('static/shapefiles/'):
				os.makedirs('static/shapefiles/')

			with open(filename, 'wb') as file:
				file.write(data)
			file.close()

			zip_ref = zipfile.ZipFile(filename, 'r')
			zip_ref.extractall('static/shapefiles/' + name + '/')
			zip_ref.close()

			temp_a = {'status': 'success'}
			sf = shapefiles(name=name, uploaded_date=date, uploaded_time=time)
			sf.save()
			
			print temp_a
		except NameError as e:
			print e
		except:
			print ('uploadzipshapefile error:', sys.exc_info()[0])
		return Response(temp_a)

@api_view(['GET'])
def webgl(request):
	if request.method == 'GET':
		dir_path = os.path.dirname(os.path.realpath(__file__))
		print dir_path
		result = {"status": "expired", "message": "Your subscription to Geocore Services has expired. Please contact a sales representative from NAVAGIS. www.navagis.com."}
		try:
			client_id = request.GET.get('client_id', '')
			result_check = check_account(client_id)
			print result_check
			if result_check:
				return Response(result) 
			with open( dir_path + '/webgl.js') as javascriptfile:
				response = HttpResponse(javascriptfile, content_type='application/javascript')
				response['Content-Disposition'] = 'attachment; filename="webgl.js"'
				return response
		except NameError as e:
			print e
			print dir_path
			return Response(result)
		except:
			print ('webgl error:', sys.exc_info()[0])
			print dir_path
			return Response(result)

def dbscan_cluster_pois(points, radius):
	res = []
	try:
		coords = np.array(points)
		kms_per_radian = 6371.0088
		epsilon = radius / kms_per_radian
		db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
		cluster_labels = db.labels_
		num_clusters = len(set(cluster_labels))
		clusters = pd.Series([ coords[cluster_labels == n] for n in range(num_clusters) ])
		centermost_points = clusters.map(get_centermost_point)
		res = centermost_points.to_json(orient='values')
	except TypeError as e1:
		print e1
	except AttributeError as e:
		print e
	except:
		print ('Unexpected error:', sys.exc_info()[0])
	return res

def get_centermost_point(cluster):
	#print cluster
	centroid = (MultiPoint(cluster).centroid.x, MultiPoint(cluster).centroid.y)
	centermost_point = min(cluster, key=lambda point: great_circle(point, centroid).m)
	res = {'count': len(cluster),'point': centermost_point, 'cluster': cluster}
	return res

def filterWithinBounds(points, bound):
	print 'Find bounds'
	pts = np.array(points)
	ur = np.array([bound[0][1], bound[0][0]])
	ll = np.array([bound[1][1], bound[1][0]])
	inidx = np.all(np.logical_and(ll <= pts, pts <= ur), axis=1)
	inbox = pts[inidx]
	res = inbox.tolist()
	return res

def cluster_navagis(points):
	try:
		clustered_result = {}
		zooms = [12, 11, 10, 9, 8, 7, 6]
		R = 6371.0088
		for zoom in zooms:
			if clustered_result:
				points = copy.deepcopy(clustered_result[str(zoom+1)])
			#radius = {'6': 80,'7': 40,'8': 20,'9': 10,'10': 6,'11': 4,'12': 2}
			radius = {'6': 160,'7': 80,'8': 40,'9': 20,'10': 10,'11': 5,'12': 3}

			val_radius = radius[str(zoom)]
			points = sorted(points, key=lambda k: k['count'], reverse=True)
			print 'Points LENGTH: ' + str(len(points)) + " for zoom: " + str(zoom)
			result_points = []
			for pointA in points:
				try:
					lat2 = radians(pointA['point'][0])
					lon2 = radians(pointA['point'][1])
					is_found = False

					for pointB in result_points:
						try:
							lat1 = radians(pointB['point'][0])
							lon1 = radians(pointB['point'][1])
							dlon = lon2 - lon1
							dlat = lat2 - lat1
							a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
							c = 2 * atan2(sqrt(a), sqrt(1 - a))
							distance = R * c

							if val_radius != 0 and distance < val_radius:
								pointB['count'] += pointA['count']
								is_found = True
								break
						except:
							print ('error outer loop:', sys.exc_info()[0])

					if is_found == False:
						result_points.append(copy.deepcopy(pointA))
				except:
					print ('error outer loop:', sys.exc_info()[0])

			clustered_result[str(zoom)] = copy.deepcopy(result_points)

			print 'End of Clustering of Zoom ...' + str(zoom) + " - result length: " + str(len(clustered_result[str(zoom)]))
	except TypeError as e:
		print 'TypeError : ' + str(e)
	except NameError as e:
		print 'NameError : ' + str(e)
	except:
		print ('error closing:', sys.exc_info()[0])
	print 'Return Clustering result ...'
	return clustered_result
