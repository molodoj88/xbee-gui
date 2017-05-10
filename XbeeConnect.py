#! /usr/bin/python
# -*- coding: utf-8 -*-
from xbee import XBee
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
            self.sendDataToForm("Connection to port {} was successful".format(self.com))
            xbee = XBee(self.ser)
            self.sendDataToForm("Send DH command to module...")
            print "Send DH command to module..."
            time.sleep(1)
            xbee.send('at', frame_id='A', command='DH')
            response = xbee.wait_read_frame()
            self.sendDataToForm("Wait for response from module...")
            print "Wait for response from module..."
            self.sleep(1)
            self.sendResponse(response['parameter'].encode("hex"))
            print response['parameter'].encode("hex")

    def sendCommand(self, command, frame_id):
        xbee = XBee(self.ser)
        xbee.send('at', frame_id=frame_id, command=str(command))
        response = xbee.wait_read_frame()
        self.sendResponse(response['parameter'].encode("hex"))

    def sendResponse(self, response):
        self.emit(QtCore.SIGNAL('SendResponse(QString)'), response)


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

