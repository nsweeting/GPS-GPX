#!/usr/bin/env python
#-*- coding: utf-8 -*-

import math
import time
import thread
import datetime
import sys


class GPX_ROUTE():

	def __init__(self, file):
		self.gpx_route           = None
		#The location of route files
		self.gpx_file            = file
		self.gpx_doc             = ''
		#Your current position and speed - needs to be updated for other calculations to work
		self.current_status      = {'lat': 0, 'lon': 0, 'speed': 0}
		#Routing switch
		self.route_mode          = False
		#Holds the current point position within the route
		self.route_position      = -1
		#Holds all data for each route point
		self.route_points        = []
		#Holds current distance of route, from current point to last point
		self.route_distance      = 0
		#Lat, lon, name, distance, and bearing of current route waypoint
		self.waypoint_info       = {'lat': 0, 'lon': 0, 'name': '', 'distance': 0, 'bearing': 0}
		#Calculated distance and bearing to current waypoint
		self.waypoint_calc       = {'distance': 0, 'bearing': 0}
		#Hour and minutes to current waypoint
		self.waypoint_eta        = {'hour': '', 'min': ''}
		#Current crosstrack error for waypoint
		self.waypoint_xte        = {'distance': '', 'dir': ''}
		self.alarm_distance      = {'waypoint': .2, 'xte': 1}
		#The total distance of current route
		self.total_distance      = 0
		#The estimated date of arrival for total route
		self.total_eta           = None
		self.sleep_time          = {'distance': 1, 'arrival': 1, 'xte': 1}

	def read_gpx(self):
		'''
		Reads the entire GPX route file, and creates a list from it.
		'''
		#Holds all the info for the current waypoint to be read
		point_info = {'lat': float(0.0), 'lon': float(0.0),'name':'','distance': float(0.0),'bearing': float(0.0)}
		#Open the gpx route file
		self.gpx_doc = open(self.gpx_file, 'r')
		con = 0
		#Run through each line of the route file
		for line in self.gpx_doc:
			line = line.lstrip()
			#Extract route point lat/long
			if line[1:6] == 'rtept' or line[1:4] == 'wpt':
				line = line.split('"')
				point_info['lat'] = float(line[1])
				point_info['lon'] = float(line[3])
				con = 1
			#Extract route point name
			elif line[1:5] == 'name' and con == 1:
				line = line.split('name>')
				point_info['name'] = line[1][:-2]
				if self.route_points:
					#Calculate the distance from the last point, to this point
					haversine_info = haversine(self.route_points[-1][0],self.route_points[-1][1],point_info['lat'],point_info['lon'])
					#Place distance in last point info
					self.route_points[-1][3] = haversine_info[0]
					self.route_points[-1][4] = haversine_info[1]
					#Add to the total distance
					self.route_distance = haversine_info[0] + self.route_distance
				self.route_points.append([point_info['lat'],point_info['lon'],point_info['name'],0,0])
				con = 0
		self.gpx_doc.close()

	def get_point(self, mode):
		'''Returns the next or last point in the route list, and moves current waypoint forward/backward

		Keyword arguments:
		mode -- determines whether to move forward (0) / backward (1)
		
		'''
		#Moves the route position forward or backward
		if mode == 0:
			self.route_position = self.route_position + 1
			if self.route_position >= len(self.route_points):
				self.route_position = self.route_position - 1
		elif mode == 1:
			self.route_position = self.route_position - 1
			if self.route_position < 0:
				self.route_position = 0
		#Recalculates the route distance
		self.calc_distance()
		#Stores the current waypoint info for easy access
		self.waypoint_info = {'lat': self.route_points[self.route_position][0], 'lon': self.route_points[self.route_position][1], 'name': self.route_points[self.route_position][2], 'distance': self.route_points[self.route_position][3], 'bearing': self.route_points[self.route_position][4]}
		#Returns the route point info
		return self.route_points[self.route_position]

	def calc_distance(self):
		'''Calculates the distance between the next route position, and all points after.'''
		#Removes the current route point from calculation
		x = self.route_position + 1
		self.route_distance = 0
		#The total number of remaining route points (-1 because of 0 list start)
		length = len(self.route_points) - 1
		#Adds the distance info
		while x < length:
			self.route_distance = self.route_distance + self.route_points[x][3]
			x += 1

	def switch(self):
		'''Checks whether Route Mode is enabled, and starts a routing, arrival and crosstrack thread if so.'''
		if self.route_mode == False:
			self.route_mode = True
			thread.start_new_thread(self.position, ())
			thread.start_new_thread(self.arrival, ())
			thread.start_new_thread(self.crosstrack, ())
			#Prevents threading errors
			time.sleep(0.1)
		else:
			self.route_mode = False

	def position(self):
		'''Used to keep track of current position in relation to current route - run as thread.'''
		#Run while routing is enabled
		while self.route_mode == True:
			#Calculates distance between current position, and destination point
			waypoint_info = haversine(self.current_status['lat'],self.current_status['lon'],self.waypoint_info['lat'],self.waypoint_info['lon'])
			self.waypoint_calc = {'distance': waypoint_info[0], 'bearing': waypoint_info[1]}
			#Calculates total route distance
			self.total_distance = self.waypoint_calc['distance'] + self.route_distance
			#Close to the destination - get the next point
			if self.waypoint_calc['distance'] < 0.02:
				self.get_point(0)
			time.sleep(self.sleep_time['distance'])

	def arrival(self):
		'''Calculates the estimated arrival time based on current speed - run as thread.'''
		#Loops until routing is turned off
		while self.route_mode == True:
			speed = round(self.current_status['speed'],2)
			#Make sure we do not divide by zero
			if speed > 0:
				time_current = datetime.datetime.now()
				#Determine time required for whole route
				time_total = self.total_distance / speed
				time_total_min, time_total_hour = math.modf(time_total)
				time_total_min = round(time_total_min*60)
				#Create a date/time object for ETA
				time_total = time_current + datetime.timedelta(hours=time_total_hour, minutes=time_total_min)
				self.total_eta = time_total.strftime("%Y-%m-%d %H:%M")
				#Determine time required for next point in route
				time_point = self.waypoint_calc['distance'] / speed
				time_point_min, time_point_hour = math.modf(time_point)
				time_point_min = round(time_point_min*60)
				#Add a 0 if minutes are less then 10
				if time_point_min < 10:
					time_point_min = '0' + str(time_point_min)
				#Remove decimal points
				self.waypoint_eta['hour'] = int(str(time_point_hour).replace('.0',''))
				self.waypoint_eta['min'] = str(time_point_min).replace('.0','')
			#Do not estimate times if speed is 0
			else:
				self.total_eta = '           --'
				self.waypoint_eta['hour'] = '--'
				self.waypoint_eta['min'] = '--'
			time.sleep(self.sleep_time['arrival'])

	def crosstrack(self):
		'''Calculates the crosstrack error for the current destination - run as thread.'''
		#Loops until routing is turned off
		while self.route_mode == True:
			#Make sure this is not the first point in the route (no standard bearing)
			if self.route_points[0][0] != self.waypoint_info['lat']:
				#Gets haversine info of last route point
				hav_start = haversine(self.route_points[self.route_position - 1][0], self.route_points[self.route_position - 1][1], self.current_status['lat'], self.current_status['lon'])
				#Crosstrack calculation
				self.waypoint_xte['distance'] = math.asin(math.sin(hav_start[0]/3443.92)*math.sin(hav_start[1]-self.route_points[self.route_position - 1][4]))*3443.92
				#Negative is left of course - making positive again
				if self.waypoint_xte['distance'] < 0:
					self.waypoint_xte['distance'] = self.waypoint_xte['distance']*(-1)
					self.waypoint_xte['dir'] = 'L'
				#Right of course
				elif self.waypoint_xte['distance'] > 0:
					self.waypoint_xte['dir'] ='R'
			#No current standard bearing
			else:
				self.waypoint_xte['distance'] = 0
				self.waypoint_xte['dir'] =''
			time.sleep(self.sleep_time['xte'])


class GPX_TRACK():

	def __init__(self,location):
		'''Readies variables for use.
		
		Keyword arguments:
		location -- the directory of the file to be made
		
		'''
		self.gpx_doc = None
		self.gpx_file = ''
		self.gpx_location = location
		self.size = 0

	def start(self, name):
		'''Creates a new track file for future use.
		
		Keyword arguments:
		name -- the name of the track info within the file
		
		'''
		print datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
		self.gpx_file = str(datetime.datetime.now().strftime('%Y-%m-%d %H%M')) + '.gpx'
		self.gpx_doc = open(self.gpx_location + self.gpx_file, 'a')
		out = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n<gpx>\n\t<trk>\n\t\t<name>' + name + '</name>\n\t\t<trkseg>\n'
		self.text_out(out)

	def point(self,lat,lon,ele,tme):
		'''Readies a track point to be outputted to the track file.
		
		Keyword arguments:
		lat -- the latitude to output
		lon -- the longitude to output
		ele -- the elevation to output
		tme -- the time to output
		
		'''
		out = '\t\t\t<trkpt lat="' + str(lat) + '" lon="' + str(lon) + '">\n' + '\t\t\t\t<ele>' + str(ele) + '</ele>\n' + '\t\t\t\t<time>' + str(tme) + '</time>\n\t\t\t</trkpt>\n'
		self.text_out(out)

	def text_out(self, out):
		'''Outputs track text to the track gpx file.
		
		Keyword arguments:
		out -- the string to be outputted
		
		'''
		self.gpx_doc.write(out)
		self.size = self.size + sys.getsizeof(out)

	def close(self):
		'''Closes the current track gpx file.'''
		out = '\t\t</trkseg>\n\t</trk>\n</gpx>'
		self.text_out(out)
		self.gpx_doc.close()


def haversine(lat_1,lon_1,lat_2,lon_2):
	'''Calculates the distance between two coordinates.
	
	Keyword arguments:
	lat_1 -- the base coordinate latitude
	lon_1 -- the base coordinate longitude
	lat_2 -- the alternate coordinate latitude
	lon_2 -- the alternate coordinate longitude
	
	'''
	#Earth radius
	try:
		radius = 3443.92
		lon_1, lat_1, lon_2, lat_2 = map(math.radians, [lon_1, lat_1, lon_2, lat_2])
		dst_lon = lon_2 - lon_1
		dst_lat = lat_2 - lat_1
		a = math.sin(dst_lat/2)**2 + math.cos(lat_1) * math.cos(lat_2) * math.sin(dst_lon/2)**2
		c = 2 * math.asin(math.sqrt(a))
		dis_out = radius * c
		y = math.sin(dst_lon) * math.cos(lat_2)
		x = math.cos(lat_1) * math.sin(lat_2) - math.sin(lat_1) * math.cos(lat_2) * math.cos(dst_lon)
		brg_out = math.degrees(math.atan2(y, x))
		brg_out = (brg_out + 360) % 360
		return [round(dis_out,2),round(brg_out)]
	except:
		pass
