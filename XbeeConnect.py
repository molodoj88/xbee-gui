#! /usr/bin/python
# -*- coding: utf-8 -*-
from xbee import XBee
from xbee.zigbee import  ZigBee
import XbeeCommands
import serial
import time
from PyQt4 import QtCore
import logging

"""
установление соединения с модулем Xbee
"""

commands = []
commands_short = []

for i in XbeeCommands.ALL_CLASSES:
    for command in [command for command in dir(i) if not command.startswith("__")]:
        c = i.__dict__.get(command)
        commands.append(c)
        commands_short.append(c.command)

commands_dict = dict(zip(commands_short, commands))

class XbeeConnect(QtCore.QThread):
    def __init__(self, form):
        QtCore.QThread.__init__(self)
        self.com = ''
        self.speed = ''
        self.ser = None
        self.prefs = []
        self.logger = None
        self.connected = False

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
            self.xbee = ZigBee(self.ser)
            self.sendDataToForm("Send DH command to module...")
            #print "Send DH command to module..."
            time.sleep(1)
            self.xbee.send('at', frame_id='A', command='VR')
            response = self.xbee.wait_read_frame()
            self.moduleConnected(response['parameter'].encode("hex"))
            #self.xbee = XBee(self.ser, callback=self.on_nd_command_cb)

    def sendCommand(self, command, frame_id):
        if str(command) == 'ND':
            self.xbee.send('at', frame_id=frame_id, command=str(command))
            response = self.xbee.wait_read_frame()
            print response
            response_list = ['source_addr', 'device_type', 'source_addr_long']

            #определение тип удаленных устройств(тест)
            if response['parameter']['device_type'].encode('hex') == '02':
                print u'оконечное устройство'
            else:
                print 'other'

            for k in response_list:

                self.sendResponse(response["parameter"][k].encode("hex"))

        else:
            self.xbee.send('at', frame_id=frame_id, command=str(command))
            response = self.xbee.wait_read_frame()
            self.sendResponse(response['parameter'].encode("hex"))

    def on_nd_command_cb(self, data):
        self.sendDataToForm(data)

    def sendResponse(self, response):
        self.emit(QtCore.SIGNAL('SendResponse(QString)'), response)

    def moduleConnected(self, response):
        self.emit(QtCore.SIGNAL('ModuleConnected(QString)'), response)


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

