GPS-GPX
=======

GPS-GPX is a python script that enables the reading of GPX route files, as well as the creation of GPX track files.

In order for this script to fully work, you must have an incoming GPS dataset - Latitude, Longitude, Speed being the crucial information. In typical setups this could be an NMEA0183 GPS connected to your computer. Th easiest way to work with this data is with another script I have created called [NMEA0183](https://github.com/nsweeting/NMEA0183). Instructions on its use are included. Once you have Lat/Long/Speed variables available, using GPS-GPX will be easy.

This project is still incomplete. The GPX tracking feature is not yet complete.

Requirements
------------

- Requires a serial NMEA0183 device or another source of GPS data.


How to Use
----------

Here is an example of using the GPX route features:
 
 ```python
import GPX

#Provide information on the GPX source file
route = GPX_ROUTE('Full/Path/To/File/Example.gpx')

#Reads the entire GPX file, and provides a list of each waypoints Name, Lat/Long, as well as distance and bearing to the next waypoint.
#Also calculates total route distance, from first to last point.
route.read_gpx()

#Holds all route waypoint info
print route.route_points
#Holds current route distance
print 'Route Distance: ',route.route_distance

#Right now, your 'current' waypoint is not set at all. In order select the first waypoint, we must move forward in the list.
#0 = forward, 1= backwards
route.get_point(0)

#'Current' waypoint info is held in the following variable
print 'Name: ',route.waypoint_info['name']
print 'Lat: ',route.waypoint_info['lat']
print 'Long: ',route.waypoint_info['lon']
print 'Distance: ',route.waypoint_info['distance']
print 'Bearing: ',route.waypoint_info['bearing']

#Holds your current position in the route list, 0 is the start
print 'Route Position: ',route.route_position

#Since our 'current' waypoint is the first in the route, we will not be able to calculate a few things, such as crosstrack error, since there is no route line.
#So lets move our 'current' waypoint forward to the second in the route list
route.get_point(0)

#Reprinting the next waypoints info
print 'Name: ',route.waypoint_info['name']
print 'Lat: ',route.waypoint_info['lat']
print 'Long: ',route.waypoint_info['lon']
print 'Distance: ',route.waypoint_info['distance']
print 'Bearing: ',route.waypoint_info['bearing']

#Now lets turn on routing calculations. We need an active NMEA0183 GPS datasource for this to work.
#We need to provide our current Lat/Long and Speed. For now, we're just going to use random numbers.
#The Lat/Long MUST be in decimal format. Speed must be in knots (the typical GPS speed output).
#These variables must be constantly updated for proper routing to function.
route.current_status['lat'] = 43.916848835
route.current_status['lat'] = -68.023909754
route.current_status['speed'] = 6.54

#Turns routing on and off.
route.switch()

#From this, 3 threads are run. One keeps track of distance, another of time, and the last for crosstrack error.
#We are now provided with the distance and bearing from our current position to the 'current' waypoint 
print 'Waypoint Distance: ',route.waypoint_calc['distance']
print 'Waypoint Bearing: ',route.waypoint_calc['bearing']

#We are also provided the total distance, from our current position, to the 'current' waypoint, as well as all points after. 
print 'Total Distance: ',route.total_distance

#Provide time for hours to be calculated
time.sleep(.1)

#We are also provided with the amount of time required to arrive from our current poisiton, to our 'current' waypoint, while going at our current speed.
print 'Waypoint Hours: ',route.waypoint_eta['hour']
print 'Waypoint Mins: ',route.waypoint_eta['min']

#We are also provided with the ETA from our current position, to the last waypoint in the route, while going at our current speed.
print 'Route ETA: ',route.total_eta

#We are also provided with the crosstrack error from our current position, to our 'current' waypoints route line. We have distance, as well as direction - left 'L' or right 'R' of the line.
print 'XTE Distance: ',route.waypoint_xte['distance']
print 'XTE Direction: ',route.waypoint_xte['dir']

#In order to control processing power, we can change the amount of time between recalculations. Default is 1 second. Below is 5 seconds.
route.time_sleep['distance'] = 5
route.time_sleep['arrival'] = 5
route.time_sleep['xte'] = 5

 ```
