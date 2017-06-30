#! /usr/bin/python
# -*- coding: utf-8 -*-
from xbee import XBee
from xbee.zigbee import ZigBee
import XbeeCommands
import serial
import time
from PyQt4 import QtCore
import json
import logging

"""
установление соединения с модулем Xbee
"""

commands = []
commands_short = []
FRAME_ID_LIST = ['1', '2', '3', '4', '5', '6', '7', '8', '9',
                 'A', 'B', 'C', 'D', 'E', 'F',
                 'G', 'I', 'J', 'K', 'O', 'P',
                 'Q', 'R', 'S', 'T', 'U', 'V',
                 'W', 'X', 'Y', 'Z']
for i in XbeeCommands.ALL_CLASSES:
    for command in [command for command in dir(i) if not command.startswith("__")]:
        c = i.__dict__.get(command)
        commands.append(c)
        commands_short.append(c.command)

commands_dict = dict(zip(commands_short, commands))

class XbeeConnect(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.com = ''
        self.speed = ''
        self.ser = None
        self.prefs = []
        self.logger = None
        self.connected = False
        self.current_frame_id = []

    def sendDataToForm(self, data):
        self.emit(QtCore.SIGNAL('SendData(QString)'), data)
        # Для теста будем распечатывать то же самое в консоли
        print self, data

    def run(self):
        # self.connectToModule()
        # Запускаем специальную тестовую функцию
        self.connectToModule()

    def connectToModule(self):
        self.sendDataToForm("Initialize Xbee...")
        print "Initialize Xbee..."
        time.sleep(1)
        try:
            self.ser = serial.Serial(self.com, self.speed)
        except Exception as ex:
            self.sendDataToForm(ex.message)
            return
        else:
            self.connected = True
            self.sendDataToForm("Connection to port {} was successful".format(self.com))
            self.xbee = ZigBee(self.ser, callback=self.on_command_cb)
            self.sendDataToForm("Send VR command to module...")
            time.sleep(1)
            self.xbee.send('at', frame_id='A', command='VR')
    def closePort(self):
        self.ser.close()
        self.sendDataToForm(u"Порт закрыт")

    def sendCommand(self, command, frame_id):

        if len(self.current_frame_id) == 0:
            frame_id = FRAME_ID_LIST[0]
            self.current_frame_id.append(frame_id)
        else:
            frame_id = FRAME_ID_LIST[len(self.current_frame_id)]
            self.current_frame_id.append(frame_id)
            print self.current_frame_id
        self.xbee.send('at', frame_id=frame_id, command=str(command))

    def sendNDCommand(self):
        self.xbee.send('at', frame_id='A', command='ND')

    def on_command_cb(self, data):
        command = data["command"]
        if command == "VR":
            self.moduleConnected(data['parameter'].encode("hex"))
        elif command == "ND":
            response_list = ['source_addr', 'device_type', 'source_addr_long']
            nd_response_dict = {key: data["parameter"][key].encode("hex") for key in response_list}
            nd_response_json = json.dumps(nd_response_dict)
            self.sendNDResponse(nd_response_json)
            print nd_response_json
        elif command == "CH":
            self.operatingChannelInfo(data["parameter"].encode("hex"))
        else:
            print data
            self.sendResponse(json.dumps(data))


    #тест отправки remote_at комаанды
    def sendIDRemoteCommmand(self):
        self.xbee.send('remote_at', frame_id='A', command='ID')


    def sendIDRemoteResponse(self, response):
        self.emit(QtCore.SIGNAL('SendIDRemoteResponse(QString)'), response)
        print response


    def sendResponse(self, response):
        self.emit(QtCore.SIGNAL('SendResponse(QString)'), response)

    def sendNDResponse(self, response):
        self.emit(QtCore.SIGNAL('SendNDResponse(QString)'), response)

    def moduleConnected(self, response):
        self.emit(QtCore.SIGNAL('ModuleConnected(QString)'), response)

    def operatingChannelInfo(self, response):
        self.emit(QtCore.SIGNAL('SendOperatingChannel(QString)'), response)


class LVL():
    """
    Сопоставление уровней логирования с числами
    """
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

