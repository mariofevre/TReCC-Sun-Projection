#!BPY
"""Registration info for Blender menus:
Name: 'Fiat Lux Ad Urbi'
Blender: 2.49b
Group: 'Wizards'
Tooltip: 'suns shadow projection and radiated surfaces patterns on any point on earth'
"""

__author__ = 'TReCC'
__version__ = '1.1'
__url__ = ["Author's site , http://www.trecc.com.ar"]
__email__=["mario@trecc.com.ar"]


######### authors ##############
#
# This program was developed from original Fiat Lux, adding the fetaures to simplify 
# building impact on sun's radiation. 
# This program is distributed under the same license acording with the original terms.
#
# Fiat Lux Copyright (C) 2008  Francesco Proietti
# http://www.netlabor.it
# francesco@netlabor.it
# alias GNUdo
#
#
# Fiat Lux ad urbi was developed by TReCC SA
#
#
################################

__bpydoc__ = """\
Usage:	set desired location, date, time in the GUI
		and this script will create an object representing
		the observer in (X,Y,Z)=(0,0,0) with a Sun lamp pointing
		towards the observer from the correct position in the sky.
		
formulas obtained from this paper:
http://www.astro.uu.nl/~strous/AA/en/reken/zonpositie.html
"""


####### BEGIN GPL LICENSE ################################################
# Copyright (C) 2011 Mario Ignacio Fevre (for TReCC SA)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
####### END GPL LICENCE ##################################################

##########################################################################################
# History
#
# Fiat Lux (by:GNUdo)
# V. 0.1 - 13-04-2008 - initial code writing
# V. 0.2 - 15-04-2008 - first public release
# V. 0.3 - 15-04-2008 - added miscellanea section
# V. 0.4 - 16-04-2008 - added previous and next week calculation
#           		corrected day calculation
# V. 0.5 - 17-04-2008 - added show sun data
# V. 0.6 - 17-04-2008 - added check to handle wrong sunrise and sunset because of wrong TZ
#			the "Now" button sets the current timezone
# V. 0.7 - 18-04-2008 - added animation support
# V. 0.8 - 10-11-2008 - added GPL License - redefined some math functions
# V. 0.9 - 12-08-2010 - sun lamp coordinates correction - by: TReCC
#
# Fiat Lux ad Urbi (by:TReCC)
# V. 1.1 - 11-01-2011 - environment GUI been added - by: TReCC
#
#           
##########################################################################################


import math
import time
import Blender
from Blender import *
from Blender import Lamp

print
print "---- Fiat Lux ad Urbi ----"

#--- Re-define some math functions to be more easily readable ---
from math import floor, radians as rad, degrees as deg, sqrt

def cos(x):
	return math.cos(rad(x))

def sin(x):
	return math.sin(rad(x))

def arcsin(x):
	return deg(math.asin(x))

def tan(x):
	return math.tan(rad(x))

def atan(x):
	return deg(math.atan(x))

def atan2(x, y):
	return deg(math.atan2(x, y))
#--- end ---

#--- transforma decimal a minutos grados (pris), minutos (mins), y segundos (secs) ---
def B10toB60(val):
	'''Converts form base 10 to base 60
	'''
	pris = int(val)
	a = val - pris
	mins = int(a * 60)
	b = a - mins / 60.0
	secs = int(round(b * 3600))
	return pris, mins, secs

def B60toB10(pris, mins, secs):
	'''Converts from base 60 to base 10
	'''
	return pris + mins / 60.0 + secs / 3600.0
	

def Greg2J(Day, Month, Year, Hour, Minute, Second):
	'''Converts from Gregorian dates to Julian dates
	'''
	time_dec = B60toB10(Hour, Minute, Second) / 24.0
	day_dec = Day + time_dec
	if Month < 3:
		Month += 12
		Year -= 1
	c = 2 - floor(Year / 100) + floor(Year / 400)
	JD = floor(1461 * (Year + 4716) / 4) + floor(153 * (Month + 1) / 5) + day_dec + c - 1524.5
	return JD

def J2Greg(JD):
	'''Converts from Julian dates to Gregorian dates
	'''
	p = floor(JD + 0.5)
	s1 = p + 68569
	n = floor(4 * s1 / 146097)
	s2 = s1 - floor((146097 * n + 3) / 4)
	i = floor(4000 * (s2 + 1) / 1461001)
	s3 = s2 - floor(1461 * i / 4) + 31
	q = floor(80 * s3 / 2447)
	e = s3 - floor(2447 * q / 80)
	s4 = floor(q / 11)
	Day = e + JD - p + 0.5
	Month = int(q + 2 - 12 * s4)
	Year = int(100 * (n - 49) + i + s4)
	fract_day = math.modf(Day)[0]
	Hour = fract_day * 24
	fract_hour = math.modf(Hour)[0]
	Minute = fract_hour * 60
	fract_minute = math.modf(Minute)[0]
	Second = fract_minute * 60
	Day = int(Day)
	Hour = int(Hour)
	Minute = int(round(Minute, 4))
	Second = int(round(Second, 4))
	return Day, Month, Year, Hour, Minute, Second

def AngleNorm(angle):
	'''Normalizes an angle between 0 and 360 degrees
	'''
	return angle % 360.0

def isBisestile(Year):
	if (Year % 100) == 0:
		if (Year % 400) == 0:
			return True
		else:
			return False
	elif (Year % 4) == 0:
		return True
	else:
		return False

def SunPos(Lat, Long, Day, Month, Year, Hour, Minute, Second, TZ, DST):
	'''Returns the Sun position from the latitude and longitude given in decimal grades
	   in the date and GMT time given, with polar coordinates
	   azimuth and elevation
	'''
	# Greenwich time
	Hour -= TZ
	Hour -= DST
	# Julian day
	JD = Greg2J(Day, Month, Year, Hour, Minute, Second)
	#JD2000 = Greg2J(1, 1, 2000, 0, 0, 0)
	JD2000 = 2451545
	# Earth mean anomaly
	M = 357.5291 + 0.98560028 * (JD - JD2000)
	M = AngleNorm(M)
	# Earth equation of center
	C = 1.9148 * sin(M) + 0.0200 * sin(2 * M) + 0.0003 * sin(3 * M)
	v = M +C
	# Sun's ecliptic coordinates
	ELong = M + 102.9372 + C + 180		# ecliptic longitude
	ELong = AngleNorm(ELong)		# ecliptic latitude
	ELat = 0
	# Sun's equatorial coordinates
	RA =  atan2(sin(ELong) * cos(23.45), cos(ELong))			# right ascension
	Decl = arcsin(sin(ELong) * sin(23.45))		# declination
	# Sidereal time at location
	ST = 280.1600 + 360.9856235 * (JD - JD2000) + Long
	ST = AngleNorm(ST)
	H = ST - RA
	# Sun's Azimuth
	azimuth = atan2(sin(H), cos(H) * sin(Lat) - tan(Decl) * cos(Lat)) + 180
	# Sun's Altitude
	altitude = arcsin(sin(Lat) * sin(Decl) + cos(Lat) * cos(Decl) * cos(H))
	#~ print
	#~ print "Julian day", JD
	#~ print "Earth mean anomaly", M, "g."
	#~ print "Earth equation of center", C, "g."
	#~ print "Sun ecliptic coordinates", ELong, "g.", ELat, "g."
	#~ print "Sun right ascension", RA, "g."
	#~ print "Sun declination", Decl, "g."
	#~ print "Sidereal time", ST, "h."
	#~ print
	#~ print "Azimuth", azimuth, "g."
	#~ print "Altitude", altitude, "g."
	return azimuth, altitude

def CreateSun(azimuth, altitude):
	''' Creates the Sun object and the Point on Earth
	'''
	global SDM, SLay
	
	curScn = Scene.GetCurrent()
	l = Lamp.New('Sun', 'Sun')		# make lamp data
	ob = Object.New('Lamp', 'Sun')		# create new lamp object
	ob.link(l)				# link lamp obj with lamp data
	sun = ob.getData()
	sun.mode |= Lamp.Modes["RayShadow"] # Enable RayShadow.
	curScn.objects.link(ob)
	# calculate and set Sun X,Y,Z coords
	d = (cos(altitude))
	ob.setLocation (SDM.val * sin(azimuth) * d, SDM.val * cos(azimuth) * d, SDM.val * sin(altitude)) # sun position
	ob.layers = [SLay.val]
	# create Point On Earth
	sunpoe = curScn.objects.new('Empty', 'SunPOE')
	sunpoe.setLocation (0, 0, 0)
	sunpoe.setSize(0.1, 0.1, 0.1)
	sunpoe.layers = [SLay.val]
	#create the constraint
	SunConstraints = ob.constraints
	SunConstLen = SunConstraints.__len__()
	SunConstraints.append(Constraint.Type.TRACKTO)
	SunPOE = SunConstraints.__getitem__(SunConstLen)
	SunPOE.name = "POE_Sun"
	# constraint settings
	SunPOE.__setitem__(Constraint.Settings.TARGET, sunpoe)
	SunPOE.__setitem__(Constraint.Settings.UP, Constraint.Settings.UPY)
	SunPOE.__setitem__(Constraint.Settings.TRACK, Constraint.Settings.TRACKNEGZ)
	
	Window.RedrawAll() # insure 3D windows are updated

def CreateSunKey(Latitude, Longitude, Day, Month, Year, Hour, Minute, Second, TZ, DST):
	''' Creates the Sun IPO Keyframe
	'''
	global SDM
	
	azimuth, altitude = SunPos(Latitude, Longitude, Day, Month, Year, Hour, Minute, Second, TZ, DST)
	d = (cos(altitude))
	sunX = SDM.val * sin(azimuth) * d
	sunY = SDM.val * cos(azimuth) * d
	sunZ = SDM.val * sin(altitude)
	
	sun_obj = Blender.Object.Get("Sun")
	sun_obj.LocX = sunX
	sun_obj.LocY = sunY
	sun_obj.LocZ = sunZ
	sun_obj.insertIpoKey(Blender.Object.LOC)

#############################################################
# GUI                                                       #
#############################################################
Latitude = Draw.Create(-34.55)
Longitude = Draw.Create(-58.47)
Year = Draw.Create(2010)
Month = Draw.Create(1)
Day = Draw.Create(1)
YearT = 0
MonthT = 6
DayT = 21
Hour = Draw.Create(0)
Minute = Draw.Create(0)
Second = Draw.Create(0)
HourT = 12
MinuteT = 0
SecondT = 0
wdT = 0
ydT = 0
DSTT = 0
DST = Draw.Create(0)
TZ = Draw.Create(-3)
SDM = Draw.Create(10)
MaxDay = 31
SLay = Draw.Create(1)
Info = Draw.Create(0)
Info1 = Draw.Create(0)
SunData = Draw.Create(0)
Singlesun = Draw.Create(0)
Anim = Draw.Create(0)
Environment = Draw.Create(0)
Solstices = Draw.Create(0)
SolsticeSum = Draw.Create(0)
SolsticeWin = Draw.Create(0)
Custom = Draw.Create(1)
Shadows = Draw.Create(1)
Radiation = Draw.Create(0)
SYear = Draw.Create(2010)
SMonth = Draw.Create(12)
SDay = Draw.Create(21)
SHour = Draw.Create(0)
SMinute = Draw.Create(0)
EYear = Draw.Create(2010)
EMonth = Draw.Create(0)
EDay = Draw.Create(0)
EHour = Draw.Create(0)
EMinute = Draw.Create(0)
Step = Draw.Create(0)
StMonth = Draw.Create(0)
StDay = Draw.Create(0)
StHour = Draw.Create(1)
StMinute = Draw.Create(0)	

y = 441
VERSION = '1.1'


def drawInfo():
	# draw instructions
	BGL.glColor3f(0.7, 0.7, 0.7)
	BGL.glRectf(3, y-56, 282, y-401)
	BGL.glColor3f(0.2, 0.2, 0.2)
	BGL.glRasterPos2d(15, y-70)
	Draw.Text("Usage instructions")
	BGL.glRasterPos2d(15, y-90)
	Draw.Text("This script will create a Sun lamp (Sun) with")
	BGL.glRasterPos2d(15, y-103)
	Draw.Text("a Track to constraint to an object called")
	BGL.glRasterPos2d(15, y-116)
	Draw.Text("SunPOE (Point on Earth).")
	BGL.glRasterPos2d(15, y-135)
	Draw.Text("The Sun will be in the exact apparent postion")
	BGL.glRasterPos2d(15, y-148)
	Draw.Text("as you see it from the selected point on")
	BGL.glRasterPos2d(15, y-161)
	Draw.Text("Earth, with North along +Y in Blender space.")
	BGL.glRasterPos2d(15, y-180)
	Draw.Text("First you have to enter the coordinates of the")
	BGL.glRasterPos2d(15, y-193)
	Draw.Text("location on Earth in decimal degrees, with")
	BGL.glRasterPos2d(15, y-206)
	Draw.Text("postive latitude going North and positive")
	BGL.glRasterPos2d(15, y-219)
	Draw.Text("Longitude going East.")
	BGL.glRasterPos2d(15, y-238)
	Draw.Text("Then insert the desired date and time manually")
	BGL.glRasterPos2d(15, y-251)
	Draw.Text("or clicking on Today (insert the current date),")
	BGL.glRasterPos2d(15, y-264)
	Draw.Text("and Now (insert current time). Don't forget to")
	BGL.glRasterPos2d(15, y-277)
	Draw.Text("set the correct Time Zone of the location and")
	BGL.glRasterPos2d(15, y-290)
	Draw.Text("the Daylight Saving Time, if valid.")
	BGL.glRasterPos2d(15, y-309)
	Draw.Text("With Sun distance multiplier you can set the")
	BGL.glRasterPos2d(15, y-322)
	Draw.Text("Sun distance into the Blender space and with")
	BGL.glRasterPos2d(15, y-335)
	Draw.Text("Sun layer you set the layer where the Sun")
	BGL.glRasterPos2d(15, y-348)
	Draw.Text("lamp and the SunPOE will be created.")
	BGL.glRasterPos2d(15, y-367)
	Draw.Text("Finally click on Create Sun and Fiat Lux! :-)")
	BGL.glRasterPos2d(15, y-387)
	Draw.Text("GNUdo")

def drawInfo1():
	# draw instructions
	BGL.glColor3f(0.7, 0.7, 0.7)
	BGL.glRectf(3, y-56, 282, y-401)
	BGL.glColor3f(0.2, 0.2, 0.2)
	BGL.glRasterPos2d(15, y-70)
	Draw.Text("Animation usage instructions")
	BGL.glRasterPos2d(15, y-90)
	Draw.Text("Before entering Anim mode make sure you")
	BGL.glRasterPos2d(15, y-103)
	Draw.Text("have an existing Sun and a SunPOE in your")
	BGL.glRasterPos2d(15, y-116)
	Draw.Text("scene.")
	BGL.glRasterPos2d(15, y-135)
	Draw.Text("Then go in the frame where the Sun will")
	BGL.glRasterPos2d(15, y-148)
	Draw.Text("start moving and 'Create Sun IPO Key'.")
	BGL.glRasterPos2d(15, y-167)
	Draw.Text("Next jump to a later frame where you want a")
	BGL.glRasterPos2d(15, y-180)
	Draw.Text("new Sun keyframe, select a new date/time")
	BGL.glRasterPos2d(15, y-193)
	Draw.Text("and 'Create Sun IPO Key' again, and so on")
	BGL.glRasterPos2d(15, y-206)
	Draw.Text("until your desired Sun motion end.")
	BGL.glRasterPos2d(15, y-225)
	Draw.Text("Alt-a on a View window and enjoy the")
	BGL.glRasterPos2d(15, y-238)
	Draw.Text("Sun moving!")
	BGL.glRasterPos2d(15, y-257)
	Draw.Text("GNUdo")
	BGL.glRasterPos2d(15, y-292)
	Draw.Text("Animation function works with object 'Sun'")
	BGL.glRasterPos2d(15, y-305)
	Draw.Text("has no efects on 'Sun.001', 'Sun.002', etc")
	BGL.glRasterPos2d(15, y-327)
	Draw.Text("TReCC")

def drawLoc():
	global Latitude, Longitude, y
	# Location
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-70)
	Draw.Text("Location on Earth")
	Latitude = Draw.Number("Latitude:", 100, 15, y-100, 180, 20, Latitude.val, -90.0, 90.0, "in decimal degrees")
	Longitude = Draw.Number("Longitude:", 100, 15, y-125, 180, 20, Longitude.val, -359.99, 359.99, "in decimal degrees")
	BGL.glRasterPos2d(210, y-87)
	Draw.Text("+ = North", 'small')
	BGL.glRasterPos2d(210, y-97)
	Draw.Text("- = South", 'small')
	BGL.glRasterPos2d(210, y-114)
	Draw.Text("+ = East", 'small')
	BGL.glRasterPos2d(210, y-124)
	Draw.Text("- = West", 'small')

def drawFixedLoc():
	global Latitude, Longitude, y
	# Location
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-70)
	Draw.Text("Location on Earth")
	#Latitude = Draw.Number("Latitude:", 100, 15, y-100, 180, 20, Latitude.val, -90.0, 90.0, "in decimal degrees")
	#Longitude = Draw.Number("Longitude:", 100, 15, y-125, 180, 20, Longitude.val, -359.99, 359.99, "in decimal degrees")
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(60, y-95)
	Draw.Text("Latitude: " + str(round(Latitude.val, 2)))
	BGL.glRasterPos2d(60, y-120)
	Draw.Text("Longitude: " + str(round(Longitude.val, 2)))
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(210, y-87)
	Draw.Text("+ = North", 'small')
	BGL.glRasterPos2d(210, y-97)
	Draw.Text("- = South", 'small')
	BGL.glRasterPos2d(210, y-114)
	Draw.Text("+ = East", 'small')
	BGL.glRasterPos2d(210, y-124)
	Draw.Text("- = West", 'small')

def drawParams():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Singlesun, Anim, Environment 
	
	# Date
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-145)
	Draw.Text("Date")
	Year = Draw.Number("Year:", 105, 15, y-175, 180, 20, Year.val, -3000, 3000, "Year")
	Month = Draw.Number("Month:", 105, 15, y-198, 180, 20, Month.val, 1, 12, "Month")
	Day = Draw.Number("Day:", 100, 15, y-222, 180, 20, Day.val, 1, MaxDay, "Day")
	Draw.PushButton("Today", 24, 200, y-175, 70, 20, "get current date")
	Draw.PushButton("Prev. Week", 44, 200, y-198, 70, 20, "Prevoius week day")
	Draw.PushButton("Next Week", 54, 200, y-222, 70, 20, "Next week day")

	# Time
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-244)
	Draw.Text("Time")
	Hour = Draw.Number("Hour:", 100, 15, y-274, 180, 20, Hour.val, 0, 23, "Hour")
	Minute = Draw.Number("Minute:", 100, 15, y-297, 180, 20, Minute.val, 0, 59, "Minute")
	Second = Draw.Number("Second:", 100, 15, y-321, 180, 20, Second.val, 0, 59, "Second")
	Draw.PushButton("Now", 34, 200, y-274, 70, 20, "get current time")
	TZ = Draw.Number("TZ:", 100, 200, y-297, 70, 20, TZ.val, -12, 12, "Time Zone")
	DST = Draw.Toggle("DST", 100, 200, y-321, 70, 20, DST.val, "Daylight saving Time")
	
	# Blender draw
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-328)
	Draw.Text("Blender draw")
	SDM = Draw.Number("Sun scale:", 100, 15, y-351, 100, 20, SDM.val, 0, 10000, "distance multiplier for blender")
	SLay = Draw.Number("Sun layer:", 100, 150, y-351, 100, 20, SLay.val, 1, 20, "layer for sun and point location")

	# Mode
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-365)
	Draw.Text("Mode")
	# Singlesun button
	Singlesun = Draw.Toggle("Single Sun", 10003, 15, y-390, 80, 20, Singlesun.val, "enter single sun mode")
	# Anim button
	Anim = Draw.Toggle("Animation", 103, 103, y-390, 80, 20, Anim.val, "enter animation mode")
	# Environmetn button
	Environment = Draw.Toggle("Environment", 1003, 191, y-390, 80, 20, Environment.val, "enter environment analisis mode")

def drawTimeStd():
	global Latitude, Longitude, y
	# Location
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-70)
	Draw.Text("Location on Earth")
	#Latitude = Draw.Number("Latitude:", 100, 15, y-100, 180, 20, Latitude.val, -90.0, 90.0, "in decimal degrees")
	#Longitude = Draw.Number("Longitude:", 100, 15, y-125, 180, 20, Longitude.val, -359.99, 359.99, "in decimal degrees")
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(15, y-85)
	Draw.Text("Latitude: " + str(round(Latitude.val, 2)))
	BGL.glRasterPos2d(15, y-100)
	Draw.Text("Longitude: " + str(round(Longitude.val, 2)))
	if Latitude > 0:
		BGL.glColor3f(1, 1, 1)
		BGL.glRasterPos2d(120, y-83)
		Draw.Text("North", 'small')
	else:
		BGL.glColor3f(1, 1, 1)
		BGL.glRasterPos2d(120, y-83)
		Draw.Text("South", 'small')		
	if Longitude > 0:
		BGL.glColor3f(1, 1, 1)
		BGL.glRasterPos2d(120, y-100)
		Draw.Text("East", 'small')
	else:
		BGL.glColor3f(1, 1, 1)
		BGL.glRasterPos2d(120, y-100)
		Draw.Text("West", 'small')	


def drawEnviron():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Singlesun, Anim, Environment, Solstices, SolsticeSum
	global SolsticeWin, Custom, Shadows, Radiation 
	
	# Time mode
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-125)
	Draw.Text("Analisis Time and Date")
	Solstices = Draw.Toggle("Solstices", 121, 15, y-150, 60, 20, Solstices.val, "Analize both solstices in the same year")
	SolsticeSum = Draw.Toggle("Summer", 122, 78, y-150, 60, 20, SolsticeSum.val, "Analize Summer solstice")
	SolsticeWin = Draw.Toggle("Winter", 123, 141, y-150, 60, 20, SolsticeWin.val, "Analize Winter solstice")
	Custom = Draw.Toggle("Custom", 124, 204, y-150, 60, 20, Custom.val, "Analize Custom period")
	
	if Custom.val == 1:
		drawTimePeriod()
	else:
		drawFixedPeriod()
	
	
		
	# Analisis type	
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-255)
	Draw.Text("Analisis Type")
	Shadows = Draw.Toggle("Shadows", 131, 15, y-280, 120, 20, Shadows.val, "Analize shadow projection")
	Radiation = Draw.Toggle("Radiation", 132, 150, y-280, 120, 20, Radiation.val, "Analize Radiated Surfaces")
	if Shadows.val == 1:
		drawMaterialsSha()
	else:
		drawMaterialsRad()

	# Mode
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-365)
	Draw.Text("Mode")
	# Singlesun button
	Singlesun = Draw.Toggle("Single Sun", 10003, 15, y-390, 80, 20, Singlesun.val, "enter single sun mode")
	# Anim button
	Anim = Draw.Toggle("Animation", 103, 103, y-390, 80, 20, Anim.val, "enter animation mode")
	# Environmetn button
	Environment = Draw.Toggle("Environment", 1003, 191, y-390, 80, 20, Environment.val, "enter environment analisis mode")
	
def drawMaterialsSha():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Singlesun, Anim, Environment, Solstices, SolsticeSum
	global SolsticeWin, Custom, Shadows, Radiation 
	
	# Asign Materials
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-305)
	Draw.Text("Assign Materials")
	Draw.Button("project selected", 16, 15, y-330, 120, 20, "Assing project layer and material to selected")
	Draw.Button("environment selected", 17, 150, y-330, 120, 20, "Assing environment layer and material to selected")

		
def drawMaterialsRad():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Singlesun, Anim, Environment, Solstices, SolsticeSum
	global SolsticeWin, Custom, Shadows, Radiation 
	
	# Asign Materials
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-305)
	Draw.Text("Assign Materials")
	Draw.Button("band 1", 18, 15, y-330, 60, 20, "Assing band 1 material to selected")
	Draw.Button("band 2", 19, 105, y-330, 60, 20, "Assing band 2 material to selected")
	Draw.Button("band 3", 20, 210, y-330, 60, 20, "Assing band 3 material to selected")
	

def drawTimePeriod():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Singlesun, Anim, Environment 
	global SYear, SMonth, SDay, SHour, SMinute, EYear, EMonth, EDay, EHour, EMinute, Step, StMonth, StDay, StHour, StMinute
	
	#start date time
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(15, y-170)
	Draw.Text("Starts at:")
	SYear = Draw.Number("", 105, 70, y-175, 50, 20, SYear.val, -3000, 3000, "Start Year")
	SMonth = Draw.Number("", 105, 125, y-175, 30, 20, SMonth.val, 1, 12, "Start Month")
	SDay = Draw.Number("", 100, 160, y-175, 30, 20, SDay.val, 1, MaxDay, "Start Day")
	SHour = Draw.Number("", 100, 200, y-175, 30, 20, SHour.val, 0, 23, "Start Hour")
	SMinute = Draw.Number("", 100, 235, y-175, 30, 20, SMinute.val, 0, 59, "Start Minute")
		
	#end date time
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(15, y-200)
	Draw.Text("Ends at:")
	EYear = Draw.Number("", 105, 70, y-205, 50, 20, EYear.val, -3000, 3000, "End Year")
	EMonth = Draw.Number("/", 105, 125, y-205, 30, 20, EMonth.val, 1, 12, "End Month")
	EDay = Draw.Number("/", 100, 160, y-205, 30, 20, EDay.val, 1, MaxDay, "End Day")
	EHour = Draw.Number("", 100, 200, y-205, 30, 20, EHour.val, 0, 23, "End Hour")
	EMinute = Draw.Number(":", 100, 235, y-205, 30, 20, EMinute.val, 0, 59, "End Minute")
	
	#step	
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(15, y-230)
	Draw.Text("Step size:")
	Step = Draw.Number("", 105, 70, y-235, 50, 20, Step.val, -3000, 3000, "step amount")
	StMonth = Draw.Toggle("Mon.", 141, 125, y-235, 35, 20, StMonth.val, "Step measured in months")
	StDay = Draw.Toggle("Day", 142, 160, y-235, 35, 20, StDay.val, "Step measured in days")
	StHour = Draw.Toggle("Hours", 143, 195, y-235, 35, 20, StHour.val, "Step measured in hours")
	StMinute = Draw.Toggle("Min", 144, 230, y-235, 35, 20, StMinute.val, "Step measured in minutes")				
	
def drawFixedPeriod():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Singlesun, Anim, Environment 
	global SYear, SMonth, SDay, SHour, SMinute, EYear, EMonth, EDay, EHour, EMinute, Step, StMonth, StDay, StHour, StMinute	
	
	#start date time
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(15, y-170)
	Draw.Text("Year:")
	SYear = Draw.Number("", 105, 70, y-175, 50, 20, SYear.val, -3000, 3000, "Start Year")

	#step
	BGL.glColor3f(0, 0, 0)
	BGL.glRasterPos2d(15, y-230)
	Draw.Text("Step size:")	
	Step = Draw.Number("", 105, 70, y-235, 50, 20, Step.val, -3000, 3000, "step amount")
	StHour = Draw.Toggle("Hours", 143, 125, y-235, 35, 20, StHour.val, "Step measured in hours")
	StMinute = Draw.Toggle("Min", 144, 160, y-235, 35, 20, StMinute.val, "Step measured in minutes")		


def drawData():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData
	# draw Sun data
	BGL.glColor3f(0.7, 0.7, 0.7)
	BGL.glRectf(3, y-56, 282, y-401)
	BGL.glColor3f(0.2, 0.2, 0.2)
	
	if Latitude.val >= 0:
		latdir = "North"
	else:
		latdir = "South"
	if Longitude.val >= 0:
		longdir = "East"
	else:
		longdir = "West"
	Lat = str(abs(round(Latitude.val, 2))) + " " + latdir
	Long = str(abs(round(Longitude.val, 2))) + " " + longdir
	
	if TZ.val >= 0:
		TZ_str = "GMT+" + str(TZ.val)
	else:
		TZ_str = "GMT" + str(TZ.val)
	
	if DST.val:
		DST_str = "DST on"
	else:
		DST_str = "DST off"
	
	Time = str(Day.val) + "/" + str(Month.val) + "/" + str(Year.val) + ", " + str(Hour.val) + ":" + str(Minute.val) + ":" + str(Second.val) + " " + TZ_str + ", " + DST_str

	BGL.glColor3f(0.0, 0.0, 0.0)
	BGL.glRasterPos2d(15, y-70)
	Draw.Text("Time and location:")
	BGL.glColor3f(0.2, 0.2, 0.2)
	BGL.glRasterPos2d(15, y-87)
	Draw.Text(Time)
	BGL.glRasterPos2d(15, y-102)
	Draw.Text("at " + Lat + ", " + Long)
	
	azimuth, altitude = SunPos(Latitude.val, Longitude.val, Day.val, Month.val, Year.val, Hour.val, Minute.val, Second.val, TZ.val, DST.val)

	BGL.glColor3f(0.0, 0.0, 0.0)
	BGL.glRasterPos2d(15, y-125)
	Draw.Text("Sun Data")
	BGL.glColor3f(0.2, 0.2, 0.2)
	BGL.glRasterPos2d(15, y-142)
	Draw.Text("Azimuth: " + str(round(azimuth,2)) + " deg.")
	BGL.glRasterPos2d(15, y-157)
	Draw.Text("Altitude: " + str(round(altitude,2)) + " deg.")

	# Noon
	alt_noon = -90.0
	for noonHour in range(6,19):
		for noonMinute in range(0,60):
			azimuth, altitude = SunPos(Latitude.val, Longitude.val, Day.val, Month.val, Year.val, noonHour, noonMinute, Second.val, TZ.val, DST.val)
			if alt_noon < altitude:
				hour_noon = noonHour
				min_noon = noonMinute
				alt_noon = altitude
			else:
				break
		if alt_noon > altitude:
			break
	if min_noon < 10:
		min_noon = "0" + str(min_noon)
	else:
		min_noon = str(min_noon)
	BGL.glRasterPos2d(15, y-175)
	Draw.Text("Noon:")
	BGL.glRasterPos2d(70, y-175)
	Draw.Text(str(hour_noon) + ":" + min_noon)

	# Sunrise
	alt_rise = 0.0
	hour_rise = "--"
	min_rise = "--"
	for riseHour in range(0,13):
		for riseMinute in range(0,60):
			azimuth, altitude = SunPos(Latitude.val, Longitude.val, Day.val, Month.val, Year.val, riseHour, riseMinute, Second.val, TZ.val, DST.val)
			if altitude < 0:
				hour_rise = riseHour
				min_rise = riseMinute
				alt_rise = altitude
			else:
				break
		if altitude > 0:
			break
	if min_rise < 10 and min_rise >= 0:
		min_rise = "0" + str(min_rise)
	else:
		min_rise = str(min_rise)
	BGL.glRasterPos2d(15, y-190)
	Draw.Text("Rise:")
	BGL.glRasterPos2d(70, y-190)
	if hour_rise == "--" or min_rise == "--":
		err = "  Is Time Zone correct?"
	else:
		err = ""
	Draw.Text(str(hour_rise) + ":" + min_rise + err)

	# Sunset
	alt_set = 0.0
	hour_set = "--"
	min_set = "--"
	for setHour in range(12,24):
		for setMinute in range(0,60):
			azimuth, altitude = SunPos(Latitude.val, Longitude.val, Day.val, Month.val, Year.val, setHour, setMinute, Second.val, TZ.val, DST.val)
			if altitude > 0:
				hour_set = setHour
				min_set = setMinute
				alt_set = altitude
			else:
				break
		if altitude < 0:
			break
	if min_set < 10:
		min_set = "0" + str(min_set)
	else:
		min_set = str(min_set)
	BGL.glRasterPos2d(15, y-205)
	Draw.Text("Set:")
	BGL.glRasterPos2d(70, y-205)
	if hour_set == "--" or min_set == "--":
		err = "  Is Time Zone correct?"
	else:
		err = ""
	Draw.Text(str(hour_set) + ":" + min_set + err)

def drawCreateIPO():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, SunData, Anim, sun_obj
	# IPO Button
	BGL.glColor3f(0.3, 0.3, 0.3)
	BGL.glRectf(3, y-401, 282, 3)
	Draw.Button("Create Sun IPO Key", 20, 15, 12, 180, 20, "create Sun IPO keyframe")

def drawCreate():
	# Create Button
	BGL.glColor3f(0.3, 0.3, 0.3)
	BGL.glRectf(3, y-401, 282, 3)
	Draw.Button("Create Sun", 15, 15, 12, 180, 20, "create Sun and location point")

def drawGenerateSeq():
	# Create Button
	BGL.glColor3f(0.3, 0.3, 0.3)
	BGL.glRectf(3, y-401, 282, 3)
	Draw.PushButton("Generate Sequence", 600, 15, 12, 180, 20, "Generate Sun Secuence")


def gui():
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global y, VERSION, SLay, Info, Info1, SunData, Anim, sun_obj
	
	BGL.glClearColor(0.5, 0.5, 0.5, 0.0)
	BGL.glClear(BGL.GL_COLOR_BUFFER_BIT)
	BGL.glColor3f(0.7, 0.7, 0.7)
	BGL.glRectf(3, y-56, 282, y-401)
	
	# Title
	BGL.glColor3f(0.2, 0.2, 0.2)
	BGL.glRectf(3, y-21, 282, y-56)
	BGL.glColor3f(1, 1, 1)
	BGL.glRasterPos2d(15, y-37)
	Draw.Text("Fiat Lux ad Urbi")
	BGL.glRasterPos2d(15, y-50)
	Draw.Text("Sun Position Calculator  v"+VERSION, "small")
	Draw.Button("Exit", 1, 237, y-47, 35, 18, 'close the script')
	# Instruction button
	Info = Draw.Toggle("Info", 101, 192, y-47, 35, 18, Info.val, "Usage instructions")
	if Info.val == 1:
		drawInfo()
		Info1 = Draw.Toggle(">>", 101, 250, 45, 20, 18, Info1.val, "Animation usage instructions")
		if Info1.val == 1:
			drawInfo1()
		drawCreate()

	# Sun Data button
	SunData = Draw.Toggle("Sun data", 102, 200, 12, 70, 20, SunData.val, "show Sun data with current parameters")
	if SunData.val == 1:
		drawData()
		drawCreate()
		
	if Info.val == 0 and SunData.val == 0 and Anim.val == 0 and Environment.val == 0:
		drawLoc()
		drawParams()
		drawCreate()
		
	if Info.val == 0 and SunData.val == 0 and Anim.val == 1 and Environment.val == 0:
		# check if Sun + SunPOE exist
		try:
			sun_obj = Blender.Object.Get("Sun")
			sunpoe_obj = Blender.Object.Get('SunPOE')
		except:
			anim_alert = Draw.PupMenu("Sun not found!%t|Make sure the Sun exists!%x1")
			Anim.val = 0
			drawLoc()
			drawParams()
			drawCreate()
		else:
			drawFixedLoc()
			drawParams()
			drawCreateIPO()
			
	elif Info.val == 0 and SunData.val == 0 and Anim.val == 0 and Environment.val == 1:
		drawTimeStd()
		drawEnviron()
		drawGenerateSeq()
		

def event(evt, val):
	if (evt == Draw.QKEY or evt == Draw.ESCKEY) and not val:
		Draw.Exit()

def bevent(evt):
	global Latitude, Longitude, Year, Month, Day, Hour, Minute, Second, TZ, DST, SDM, MaxDay
	global Info, SLay, SunData, y, Anim
	if evt == 1:
		Draw.Exit()
	elif evt == 15:
		azimuth, altitude = SunPos(Latitude.val, Longitude.val, Day.val, Month.val, Year.val, Hour.val, Minute.val, Second.val, TZ.val, DST.val)
		CreateSun(azimuth, altitude)
		print "sun created"
		print
	elif evt == 20:
		CreateSunKey(Latitude.val, Longitude.val, Day.val, Month.val, Year.val, Hour.val, Minute.val, Second.val, TZ.val, DST.val)
	elif evt == 24:
		YearT, MonthT, DayT, HourT, MinuteT, SecondT, wdT, ydT, DSTT = time.localtime()
		Year.val = YearT
		Month.val = MonthT
		Day.val = DayT
		DST.val = DSTT
		Draw.Redraw()
	elif evt == 34:
		YearT, MonthT, DayT, HourT, MinuteT, SecondT, wdT, ydT, DSTT = time.localtime()
		Hour.val = HourT
		Minute.val = MinuteT
		Second.val = SecondT
		DST.val = DSTT
		TZ.val = (-time.timezone / 3600)
		Draw.Redraw()
	elif evt == 44:
		JD_pw = Greg2J(Day.val-7, Month.val, Year.val, Hour.val, Minute.val, Second.val)
		Day.val, Month.val, Year.val, Hour.val, Minute.val, Second.val = J2Greg(JD_pw)
		Draw.Redraw()
	elif evt == 54:
		JD_pw = Greg2J(Day.val+7, Month.val, Year.val, Hour.val, Minute.val, Second.val)
		Day.val, Month.val, Year.val, Hour.val, Minute.val, Second.val = J2Greg(JD_pw)
		Draw.Redraw()
	elif evt == 100:
		Draw.Redraw()
	elif evt == 101:
		SunData.val = 0
		Anim.val = 0
		Draw.Redraw()
	elif evt == 102:
		Info.val = 0
		Anim.val = 0
		Draw.Redraw()
	elif evt == 103:
		Info.val = 0
		SunData.val = 0
		Environment.val = 0
		Singlesun.val = 0
		Draw.Redraw()
	elif evt == 1003:
		Info.val = 0
		SunData.val = 0
		Anim.val = 0
		Singlesun.val = 0
		Draw.Redraw()
	elif evt == 10003:
		Info.val = 0
		SunData.val = 0
		Environment.val = 0
		Anim.val = 0		
		Draw.Redraw()	
	elif evt == 105:
		if Month.val == 1 or Month.val == 3 or Month.val == 5 or Month.val == 7 or Month.val == 8 or Month.val == 10 or Month.val == 12:
			MaxDay = 31
		elif Month.val == 2:
			if isBisestile(Year.val):
				MaxDay = 29
			else:
				MaxDay = 28
		else:
			MaxDay = 30
		Draw.Redraw()

	# toggle entre radiacion y sombras
	elif evt == 131:
		Radiation.val = 0
		Draw.Redraw()			
	elif evt == 132:
		Shadows.val = 0
		Draw.Redraw()	

	# toggle entre solsticios
	elif evt == 121:
		SolsticeSum.val = 0
		SolsticeWin.val = 0
		Custom.val = 0
		Draw.Redraw()			
	elif evt == 122:
		Solstices.val = 0
		SolsticeWin.val = 0
		Custom.val = 0
		Draw.Redraw()		
	elif evt == 123:
		Solstices.val = 0
		SolsticeSum.val = 0
		Custom.val = 0
		Draw.Redraw()	
	elif evt == 124:
		Solstices.val = 0
		SolsticeSum.val = 0
		SolsticeWin.val = 0
		Draw.Redraw()	
		
	# toggle entre tiempo step
	elif evt == 141:
		StDay.val = 0
		StHour.val = 0
		StMinute.val = 0
		Draw.Redraw()			
	elif evt == 142:
		StMonth.val = 0
		StHour.val = 0
		StMinute.val = 0
		Draw.Redraw()	
	elif evt == 143:
		StMonth.val = 0
		StDay.val = 0
		StMinute.val = 0
		Draw.Redraw()	
	elif evt == 144:
		StMonth.val = 0
		StDay.val = 0
		StHour.val = 0
		Draw.Redraw()	




Draw.Register(gui, event, bevent)





