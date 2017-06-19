# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
import datetime
from XbeeConnect import XbeeConnect
import logging
import XbeeCommands
import random
import json
from time import sleep

module_type_dict = {'20': 'ZigBee Coordinator AT',
                    '21': 'ZigBee Coordinator API',
                    '22': 'ZigBee Router AT',
                    '23': 'ZigBee Router API',
                    '26': 'ZigBee Router/End Device, Analog I/O Adapter',
                    '27': 'ZigBee Router/End Device, Digital I/O Adapter',
                    '28': 'ZigBee End Device AT',
                    '29': 'ZigBee End Device API'}
commands = []
commands_dict = {}
for i in XbeeCommands.ALL_CLASSES:
    for command in [command for command in dir(i) if not command.startswith("__")]:
        commands.append(command)
        commands_dict[command] = i.__dict__.get(command)


#Главное окно
class Block(QtGui.QMainWindow, QtGui.QTreeView):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.centralWidget = QtGui.QWidget()
        self.input_data()
        self.setCentralWidget(self.centralWidget)
        self.resize(800, 600)
        self.setWindowTitle('Zigbee')
        self.setWindowIcon(QtGui.QIcon("zigbee.png"))
        self.tabWidget = QtGui.QTabWidget()
        self.centralWidgetLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.centralWidgetLayout.addWidget(self.tabWidget)
        """ Вкладка подключение """
        self.tab1 = QtGui.QWidget()
        """ Вкладка управление """
        self.tab2 = QtGui.QWidget()
        """ Вкладка построение сети """
        self.tab3 = QtGui.QWidget()
        self.tabWidget.addTab(self.tab1, u'Подключение')
        self.tabWidget.addTab(self.tab2, u'Управление')
        self.tabWidget.addTab(self.tab3, u'Структура сети')
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        self.optios_log()
        self.status_bar()
        self.all_tab()

    """ Входные данные """

    def input_data(self):
        self.coor = None
        self.connPrefs = []
        self.form = self
        self.module_type = ''

    """ Все вкладки """

    def all_tab(self):
        self.tab_connect()
        self.tab_control()
        self.tab_network_structure()

    """ Вкладка Подключение """

    def tab_connect(self):
        tab1_Layout = QtGui.QHBoxLayout(self.tab1)
        options_connect = QtGui.QGroupBox(u'Параметры подключения')
        description_st_connect = QtGui.QGroupBox(u'Дополнительная информация')
        tab1_Layout.addWidget(options_connect)
        tab1_Layout.addWidget(description_st_connect, QtCore.Qt.AlignCenter)
        options_layout = QtGui.QHBoxLayout(options_connect)
        list_param = QtGui.QWidget()
        options_layout.addWidget(list_param)
        options_layout.addWidget(QtGui.QWidget())
        list_param.setLayout(self.grid)
        description_layout = QtGui.QVBoxLayout(description_st_connect)
        status_connect = QtGui.QGroupBox(u'Статус подключения')
        list_devices = QtGui.QGroupBox(u'ZigBee устройства')
        description_layout.addWidget(status_connect)
        description_layout.addWidget(list_devices, QtCore.Qt.AlignCenter)
        self.st_connect_layout = QtGui.QHBoxLayout()
        list_dev_layout = QtGui.QHBoxLayout(list_devices)
        coor = QtGui.QGroupBox(u'Кооридантор')
        router = QtGui.QGroupBox(u'Роутер')
        end_device = QtGui.QGroupBox(u'Оконечное устройство')
        list_dev_layout.addWidget(coor)
        list_dev_layout.addWidget(router)
        list_dev_layout.addWidget(end_device)
        self.parameter_connecting()

        #иконка

        self.conn_off_icon = QtGui.QPixmap('images/red_led.png')
        self.conn_on_icon = QtGui.QPixmap('images/green_led.png')
        self.labelForIcon = QtGui.QLabel()
        self.Icon_lbl = QtGui.QLabel(self.module_type)
        self.st_connect_layout.addWidget(self.Icon_lbl)
        self.labelForIcon.setPixmap(self.conn_off_icon)
        self.st_connect_layout.addWidget(self.labelForIcon)
        status_connect.setLayout(self.st_connect_layout)
        #self.connected = True

    """ Парамметры подключения, для 1-ой вкладки"""
    def parameter_connecting(self):
        com_lbl = QtGui.QLabel('COM')
        com_list = QtGui.QComboBox()
        com_list.setFixedWidth(80)
        com_list.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        self.grid.addWidget(com_list, 1, 1)
        speed_lbl = QtGui.QLabel('Speed')
        speed_list = QtGui.QComboBox()
        speed_list.setFixedWidth(80)
        speed_list.addItems(["9600", "115200"])
        self.grid.addWidget(speed_list, 2, 1)
        data_bits_lbl = QtGui.QLabel('Data bits')
        data_bits_list = QtGui.QComboBox()
        data_bits_list.setFixedWidth(80)
        data_bits_list.addItems(["5", "6", "7", "8"])
        self.grid.addWidget(data_bits_list, 3, 1)
        stop_bit_lbl = QtGui.QLabel('Stop bit')
        stop_bit_list = QtGui.QComboBox()
        stop_bit_list.setFixedWidth(80)
        stop_bit_list.addItems(["1", "2"])
        self.grid.addWidget(stop_bit_list, 4, 1)
        parity_lbl = QtGui.QLabel('Parity')
        parity_list = QtGui.QComboBox()
        parity_list.setFixedWidth(80)
        parity_list.addItems(["None", "Odd", "Even", "Mark", "Space"])
        self.grid.addWidget(parity_list, 5, 1)
        flow_control_lbl = QtGui.QLabel('Flow Control')
        flow_control_list = QtGui.QComboBox()
        flow_control_list.setFixedWidth(80)
        flow_control_list.addItems(["None", "XOnXOff", "Request To Send", "Request To SendXOnXOff"])
        self.grid.addWidget(flow_control_list, 6, 1)
        self.connecting_btn = QtGui.QPushButton(u"Соединение")
        self.grid.addWidget(self.connecting_btn, 7, 0)
        self.grid.addWidget(com_lbl, 1, 0)
        self.grid.addWidget(speed_lbl, 2, 0)
        self.grid.addWidget(data_bits_lbl, 3, 0)
        self.grid.addWidget(stop_bit_lbl, 4, 0)
        self.grid.addWidget(parity_lbl, 5, 0)
        self.grid.addWidget(flow_control_lbl, 6, 0)
        com_lbl.resize(500, com_lbl.height())
        self.connPrefFiels = [com_list, speed_list, data_bits_list, stop_bit_list, parity_list, flow_control_list]

    """ Вкладка управление """

    def tab_control(self):
        tab2_layout = QtGui.QHBoxLayout(self.tab2)
        send_commands = QtGui.QGroupBox(u'Отправка команды')
        list_commands = QtGui.QGroupBox(u'Выбор команды')
        tab2_layout.addWidget(send_commands)
        tab2_layout.addWidget(list_commands, QtCore.Qt.AlignLeft)
        send_commands_layout = QtGui.QGridLayout(send_commands)
        self.list_commands_layout = QtGui.QHBoxLayout(list_commands)
        self.list_all_commands()
        type_commands_lbl = QtGui.QLabel(u'Тип команды')
        send_commands_layout.addWidget(type_commands_lbl, 1, 0)
        list_type_commands = QtGui.QComboBox()
        list_type_commands.setFixedWidth(80)
        list_type_commands.addItems(["AT", "Remote AT"])
        send_commands_layout.addWidget(list_type_commands, 1, 1)
        command_lbl = QtGui.QLabel(u'Команда')
        send_commands_layout.addWidget(command_lbl, 2, 0)
        self.comm_edit = QtGui.QLineEdit()
        self.comm_edit.setFixedWidth(80)

        """ Автодополнения команд """

        model = QtGui.QStringListModel()
        model.setStringList(commands)
        completer = QtGui.QCompleter()
        completer.setCaseSensitivity(0)
        completer.setModel(model)
        self.comm_edit.setCompleter(completer)
        send_commands_layout.addWidget(self.comm_edit, 2, 1)
        parameter_lbl = QtGui.QLabel(u'Параметры')
        send_commands_layout.addWidget(parameter_lbl, 3, 0)
        comm_parameter_edit = QtGui.QLineEdit()
        comm_parameter_edit.setFixedWidth(80)
        send_commands_layout.addWidget(comm_parameter_edit, 3, 1)
        self.send_command_btn = QtGui.QPushButton(u'Отправить')
        send_commands_layout.addWidget(self.send_command_btn, 4, 0)
        self.send_command_btn.clicked.connect(self.send_btn_clicked)

    """ Список доступных команд """

    def list_all_commands(self):
        self.commands_list_model = QtGui.QStandardItemModel()
        self.view = QtGui.QTreeView()
        self.view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.view.setModel(self.commands_list_model)
        self.commands_list_model.setHorizontalHeaderLabels([u'Команда'])
        parent = self.commands_list_model.invisibleRootItem()
        for c in XbeeCommands.ALL_CLASSES:
            class_name_item = QtGui.QStandardItem(c.__name__[1:])
            parent.appendRow(class_name_item)
            for c_item in [QtGui.QStandardItem(c) for c in dir(c) if not c.startswith("__")]:
                class_name_item.appendRow(c_item)
        self.list_commands_layout.addWidget(self.view)

        def on_item_clicked(index):
            command_str = str(index.data().toString())
            if index.parent().column() == 0:
                self.comm_edit.setText(commands_dict[command_str].command)

        self.connect(self.view, QtCore.SIGNAL("clicked(const QModelIndex&)"), on_item_clicked)

    """ Логирование """

    def optios_log(self):
        self.logWidget = QTextEditLogger(self)
        self.logWidget.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S"))
        logging.getLogger().addHandler(self.logWidget)
        logging.getLogger().setLevel(logging.DEBUG)

        """Сохранение логов в файл"""

        name_file_log = logging.FileHandler('test.log')
        name_file_log.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        name_file_log.setFormatter(formatter)
        logging.getLogger().addHandler(ch)
        logging.getLogger().addHandler(name_file_log)
        self.centralWidgetLayout.addWidget(self.logWidget.widget)
        logging.debug("Logger initialized")

    def tab_network_structure(self):
        """Функция для инициализации третьей вкладки (структура сети)"""

        self.update_network_btn = QtGui.QPushButton(u"Обновить")
        self.scene = QtGui.QGraphicsScene(parent=self.tab3)
        self.scene_view = QtGui.QGraphicsView(self.scene)
        self.scene_view_widget = QtGui.QVBoxLayout(self.tab3)
        self.scene_view_widget.addWidget(self.update_network_btn)
        self.scene_view_widget.addWidget(self.scene_view)
        self.connect(self.connecting_btn, QtCore.SIGNAL("clicked()"), lambda fields=self.connPrefFiels: self.readPrefs(fields))
        self.update_network_btn.clicked.connect(self.on_update_network_btn_clicked)
        self.tabWidget.currentChanged.connect(self.hide_log)

    def status_bar(self):
        """ Верхнее меню управления """

        menubar = self.menuBar()
        file = menubar.addMenu(u'Файл')
        file.addAction(u'Открыть соединение')
        file.addAction(u'Сохранить логи')
        file.addAction(u'Закрыть')
        edit = menubar.addMenu(u'Правка')
        edit.addAction(u'Отправить команду')
        conn = menubar.addMenu(u'Подключение')
        help = menubar.addMenu(u'Справка')
        help.addAction(u'О программе')
        help.addAction(u'Список АТ-команд')
        exit = menubar.addMenu(u'Выход')

    def hide_log(self, ss):
        if ss == 2:
            self.logWidget.widget.setVisible(False)
        else:
            self.logWidget.widget.setVisible(True)
    #функция для кнопки которая выводит дату и время выполнения команды
    def btn2click(self):
        time = str(datetime.datetime.now())
        logging.debug(time + " New text string")

#TODO В данной функции хотел сделать следующее: перехватит отправку сообщений в форму и выводить соответствующий индикатор:

    #Функция индикации подключения
    def connectionIndicate(self, firmware):

        self.Icon_lbl.setText(module_type_dict[str(firmware[:2])])

        firm_id = str(firmware[:2])

        if firm_id == '21':
            self.coord = QtGui.QPixmap('images/zc.png')
            self.coor_item = QtGui.QGraphicsPixmapItem(self.coord, scene=self.scene)
            self.coor_item.setOffset(100, 300)

        self.labelForIcon.setPixmap(self.conn_on_icon)


    def structure_network(self):
       pass

    #функция считавания значений для подключения модуля
    def readPrefs(self, fields):
        self.connPrefs = []
        for i in fields:
            item = i.itemText(i.currentIndex())
            self.connPrefs.append(item)

        # отправляем в поток параметры подключения
        # стартуем
        self.coor = XbeeConnect()
        self.coor.com = str("COM" + self.connPrefs[0])
        self.coor.speed = int(self.connPrefs[1])
        self.connect(self.coor, QtCore.SIGNAL('SendData(QString)'), self.logMessage, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('SendResponse(QString)'),
                     self.logMessage, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('SendNDResponse(QString)'),
                     self.update_network_structure, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('ModuleConnected(QString)'),
                     self.connectionIndicate, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('SendOperatingChannel(QString)'),
                     self.operating_channel_indicate, QtCore.Qt.QueuedConnection)
        self.coor.start()

    def send_btn_clicked(self):
        _command = self.comm_edit.text()
        self.logMessage(_command)
        self.coor.sendCommand(_command, 'A')

    def on_update_network_btn_clicked(self):
        self.coor.sendNDCommand()

    def operating_channel_indicate(self, channel):
        operating_channel_name_lbl = QtGui.QLabel(u"Канал: ")
        operating_channel_lbl = QtGui.QLabel()
        self.st_connect_layout.addWidget(operating_channel_name_lbl)
        self.st_connect_layout.addWidget(operating_channel_lbl)
        operating_channel_lbl.setText(channel)

    def update_network_structure(self, response):
        response_dict = json.loads(str(response))
        if response_dict["device_type"] == "01":
            self.router = QtGui.QPixmap('images/zr.png')
            self.router_item = QtGui.QGraphicsPixmapItem(self.router, scene=self.scene)
            self.router_item.setOffset(500, 100)
        if response_dict["device_type"] == "02":
            x = random.randrange(50, 800)
            y = random.randrange(50, 600)
            self.end_dev = QtGui.QPixmap('images/ze.png')
            self.end_item = QtGui.QGraphicsPixmapItem(self.end_dev, scene=self.scene)
            self.end_item.setOffset(x, y)


    def logMessage(self, text):
        logging.debug(text)

class QTextEditLogger(logging.Handler):
    """
    Обработчик для логгера. Выводит сообщения логгера в QTextEdit на форме
    """
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.widget = QtGui.QTextEdit()
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)


def main():
    app = QtGui.QApplication(sys.argv)
    bl = Block()
    bl.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
