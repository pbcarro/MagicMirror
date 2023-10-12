import json
import requests
import datetime
import time
import sys
from PyQt5.QtWidgets import QApplication,  QLabel, QWidget, QGridLayout, QVBoxLayout, QSizePolicy
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QFontMetrics,QPixmap

#import config

class Train:
	def __init__(self,ParentLabel,TextLabel,Station,WalkTime=480,MaxWindow=3600):
		self.Now = datetime.datetime.now()
		self.Error = False
		self.WalkTime = WalkTime
		self.MaxWindow = MaxWindow
		self.ParentLabel = ParentLabel
		self.TextLabel = TextLabel
		self.Departures = []
		if (Station == "North"): self.Station = 70066
		else: self.Station = 70065	#Just forcing it to be southbound unless it's definitely north
		self.QueryDelay = 10 #The minimum time between queries to keep from exceeding the limit, can be sidestepped with an api key that I need to add
		self.Ticks = 0
		
	def Get_T_Departure (self,QueryType):
		Now = datetime.datetime.now()
		if (QueryType == 1): 
			QueryString = "schedules"
		else:
			QueryString = "predictions"
		try :
			contentPage = json.loads((requests.get("https://api-v3.mbta.com/%s?filter[stop]=%d" % (QueryString,self.Station))).text)		
		except:
			self.Error = True
			self.Departures = []
			return
		if ("errors" in contentPage):
			self.Error = True
			self.Departures = []
			return 
		Times = []
		for Item in contentPage['data']:
			if (Item['attributes']['departure_time'] == None):
				self.Error = True
				self.Departures = []
			else:	
				DepartureTime = datetime.datetime.strptime(Item['attributes']['departure_time'][:18],"%Y-%m-%dT%H:%M:%S")	#cycle through the list of predictions and grab the predicted departure times
				TimetoDepart = (DepartureTime-Now).total_seconds()		#Get the time till the train departs in seconds, cause timedelta doesnt do minutes
				if ((TimetoDepart > self.WalkTime) and (TimetoDepart < self.MaxWindow)): Times.append(DepartureTime)	#If there is a train leaving in the next hour and more than the 8 minute walk time to the station we keep it
		if (len(Times) > 2): 
			#if (QueryType == 1):
			self.Departures.sort(reverse=True,key=SecondsFromNow)
			self.Departures = Times[:2]	#I only care about the next two trains max
			return 
		else: 
			self.Departures = Times
			return

	def Update_DepartureTimes (self):
		self.Ticks +=1
		Now = datetime.datetime.now()
		if ((self.Ticks % self.QueryDelay) == 0):
			self.Ticks = 0
			self.Get_T_Departure(0)
			if (len(self.Departures) <= 0):
				self.Get_T_Departure(1)
				self.TextLabel.setStyleSheet("color : blue;")
			else:
				self.TextLabel.setStyleSheet("color : white;")
		if (len(self.Departures) < 1):
			self.ParentLabel.setText("--:--")
			self.ParentLabel.setStyleSheet("color : white;")
			self.TextLabel.setStyleSheet("color : white;")
		else:	
			Min,Sec = Sec_to_Min ((self.Departures[0]-Now).total_seconds()-self.WalkTime)
			if (Min < 1):
				self.ParentLabel.setStyleSheet("color : red;")
			else:
				self.ParentLabel.setStyleSheet("color : white;")
			self.ParentLabel.setText("%d:%02d" % (Min,Sec))

class TClock:
	def __init__ (self,InputWidget):
		self.SizeX = 400
		self.SizeY = 150

def Sec_to_Min (Seconds):
	Min = int(Seconds/60)	#Keep the minutes in int
	Sec = Seconds%60.0		#seconds as float
	return Min,Sec

def SecondsFromNow (Time):
	Now = datetime.datetime.now()
	return(Time-Now).total_seconds()

app = QApplication(sys.argv)
w = QWidget()
w.resize(400,150)
w.setStyleSheet("background-color: black; color : white;")
w.move(300,300)
w.MinSecLabel = QLabel("--:--")
w.MinSecLabel2 = QLabel("--:--")
w.TrainLabel1 = QLabel("Time to Northbound Departure")
w.TrainLabel2 = QLabel("Time to Southbound Departure")
w.clockLayout = QGridLayout()
w.clockLayout.addWidget(w.MinSecLabel, 1, 5, 1, 1, QtCore.Qt.AlignRight)
w.clockLayout.addWidget(w.TrainLabel1, 1, 1, 1, 4, QtCore.Qt.AlignLeft)
w.clockLayout.addWidget(w.MinSecLabel2, 2, 5, 1, 1, QtCore.Qt.AlignRight)
w.clockLayout.addWidget(w.TrainLabel2, 2, 1, 1, 4, QtCore.Qt.AlignLeft)

font = QFont()
font.setPointSize(20)
font.setBold(1)

w.MinSecLabel.setFont(font)
w.MinSecLabel2.setFont(font)
w.TrainLabel1.setFont(font)
w.TrainLabel2.setFont(font)

timer = QTimer(w)
timer2 = QTimer(w)
North = Train (ParentLabel=w.MinSecLabel,TextLabel=w.TrainLabel1,Station="North")
South = Train (ParentLabel=w.MinSecLabel2,TextLabel=w.TrainLabel2,Station="South")

Test = QPixmap("500px-MBTA_Invert.png").scaledToWidth(64)
Test2 = QLabel()
Test2.setPixmap(Test)
w.clockLayout.addWidget(Test2, 1, 6, 2, 2, QtCore.Qt.AlignRight)

w.setLayout(w.clockLayout)

timer.timeout.connect(North.Update_DepartureTimes)
timer.start(1000)
timer2.timeout.connect(South.Update_DepartureTimes)
timer2.start(1000)
w.setWindowTitle("Test MBTA Clock Display")
w.show()
sys.exit(app.exec_())
