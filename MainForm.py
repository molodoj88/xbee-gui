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

"""Дополнительное окно для настроек удаленных устройств"""
class ModalWind(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ModalWind, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowSystemMenuHint)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setWindowTitle(u'Управление удаленным устройством')
        self.resize(550, 300)
        self.send_remote_command_btn = QtGui.QPushButton(u'Отправить')
        modal_grid_widget = QtGui.QWidget()
        modal_layout = QtGui.QHBoxLayout(self)
        modal_grid = QtGui.QGridLayout(modal_grid_widget)
        modal_layout.addWidget(modal_grid_widget)
        modal_grid.addWidget(self.send_remote_command_btn, 4, 0)
        remote_command_lbl = QtGui.QLabel(u'Команда')
        self.remote_command_edit = QtGui.QLineEdit()
        remote_parameter_lbl = QtGui.QLabel(u'Параметр')
        remote_parameter_edit = QtGui.QLineEdit()
        type_commands_lbl_mod = QtGui.QLabel(u'Тип команды')
        modal_grid.addWidget(type_commands_lbl_mod, 1, 0)
        self.list_type_commands_mod = QtGui.QComboBox()
        self.list_type_commands_mod.setFixedWidth(80)
        self.list_type_commands_mod.addItems(["at", "remote_at"])
        modal_grid.addWidget(self.list_type_commands_mod, 1, 1)
        modal_grid.addWidget(self.remote_command_edit, 2, 1, QtCore.Qt.AlignLeft)
        modal_grid.addWidget(remote_parameter_lbl, 3, 0, QtCore.Qt.AlignLeft)
        modal_grid.addWidget(remote_parameter_edit, 3, 1, QtCore.Qt.AlignLeft)
        modal_grid.addWidget(remote_command_lbl, 2, 0, QtCore.Qt.AlignLeft)
        modal_right_widget = QtGui.QWidget()
        modal_layout.addWidget(modal_right_widget)
        modal_all_commands_widget = AllCommandsListWidget(self.remote_command_edit)
        modal_layout.addWidget(modal_all_commands_widget)

class AllCommandsListWidget(QtGui.QWidget):
    def __init__(self, command_edit, parent=None):
        super(AllCommandsListWidget, self).__init__(parent)
        self.commands_list_model = QtGui.QStandardItemModel()
        self.view = QtGui.QTreeView()
        self.view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.view.setModel(self.commands_list_model)
        self.commands_list_model.setHorizontalHeaderLabels([u'Выберите команду'])
        parent = self.commands_list_model.invisibleRootItem()
        for c in XbeeCommands.ALL_CLASSES:
            class_name_item = QtGui.QStandardItem(c.__name__[1:])
            parent.appendRow(class_name_item)
            for c_item in [QtGui.QStandardItem(c) for c in dir(c) if not c.startswith("__")]:
                class_name_item.appendRow(c_item)
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.view)

        def on_item_clicked(index):
            command_str = str(index.data().toString())
            if index.parent().column() == 0:
                command_edit.setText(commands_dict[command_str].command)

        self.connect(self.view, QtCore.SIGNAL("clicked(const QModelIndex&)"), on_item_clicked)

"""Главное окно"""
class mainWindow(QtGui.QMainWindow, QtGui.QTreeView):
    "Инициализация основного окна и подключение всех элементов приложения"
    def __init__(self, parent=None):
        super(mainWindow, self).__init__(parent)
        QtGui.QWidget.__init__(self, parent)
        self.centralWidget = QtGui.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.resize(800, 600)
        self.setWindowTitle('Zigbee')
        self.setWindowIcon(QtGui.QIcon("zigbee.png"))
        self.input_data()
        self.main_tab()
        self.options_log()
        self.status_bar()
        self.all_tabs()
        self.graphics_scene_items = dict()

    "Инициализация основного таба и 3х вкладок(подключение, управление, структура сети)"
    def main_tab (self):
        self.tabWidget = QtGui.QTabWidget()
        self.centralWidgetLayout = QtGui.QVBoxLayout(self.centralWidget)
        self.centralWidgetLayout.addWidget(self.tabWidget)
        """ Вкладка подключение """
        self.tab1 = QtGui.QWidget()
        """ Вкладка управление """
        self.tab2 = QtGui.QWidget()
        """ Вкладка построение сети """
        self.tab3 = QtGui.QWidget()
        self.tabWidget.addTab(self.tab1, u'Соединение')
        self.tabWidget.addTab(self.tab2, u'Управление')
        self.tabWidget.addTab(self.tab3, u'Структура сети')
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)

    "Верхнее меню управления"
    def status_bar(self):
        menubar = self.menuBar()
        file = menubar.addMenu(u'Файл')
        file.addAction(u'Открыть соединение')
        file.addAction(u'Сохранить логи')
        file.addAction(u'Закрыть', self.close)
        edit = menubar.addMenu(u'Правка')
        edit.addAction(u'Отправить команду')
        conn = menubar.addMenu(u'Подключение')
        help = menubar.addMenu(u'Справка')
        help.addAction(u'О программе')
        help.addAction(u'Список АТ-команд')
        exit = menubar.addMenu(u'Выход')

    """ Входные данные """
    def input_data(self):
        self.coor = None
        self.connPrefs = []
        self.form = self
        self.module_type = ''

    """ Все вкладки """
    def all_tabs(self):
        self.tab_connect()
        self.tab_control()
        self.tab_network_structure()

    """ Вкладка соединение """
    def tab_connect(self):
        tab_connect_layout = QtGui.QHBoxLayout(self.tab1)
        options_connect = QtGui.QGroupBox(u'Настройки COM порта')
        description_status_connect = QtGui.QGroupBox(u'Дополнительная информация')
        start_settings_module = QtGui.QGroupBox(u'Быстрая настройка модуля')
        start_settings_module.setFixedWidth(210)
        options_connect.setFixedWidth(235)

        tab_connect_layout.addWidget(options_connect)
        tab_connect_layout.addWidget(start_settings_module)
        tab_connect_layout.addWidget(description_status_connect)

        options_layout = QtGui.QHBoxLayout(options_connect)

        start_settings_layout = QtGui.QGridLayout(start_settings_module)
        pan_id_label = QtGui.QLabel('PAN ID')
        name_module_label = QtGui.QLabel(u'Имя модуля')
        channel_on_off = QtGui.QLabel(u'Канал связи')
        start_settings_layout.addWidget(pan_id_label, 1, 0)
        start_settings_layout.addWidget(name_module_label, 2, 0)
        start_settings_layout.addWidget(channel_on_off, 3, 0)

        self.pan_id_edit = QtGui.QLineEdit()
        self.pan_id_edit.setFixedWidth(50)
        start_settings_layout.addWidget(self.pan_id_edit, 1, 1)
        self.send_commandId_btn = QtGui.QPushButton(u'ок')
        start_settings_layout.addWidget(self.send_commandId_btn, 1, 2)
        self.send_commandId_btn.clicked.connect(self.send_id_command_clicked)

        self.name_edit = QtGui.QLineEdit()
        self.name_edit.setFixedWidth(50)
        start_settings_layout.addWidget(self.name_edit, 2, 1)
        self.send_commandNI_btn = QtGui.QPushButton(u'ок')
        start_settings_layout.addWidget(self.send_commandNI_btn, 2, 2)
        self.send_commandNI_btn.clicked.connect(self.send_ni_command_clicked)

        self.channel_edit = QtGui.QLineEdit()
        self.channel_edit.setFixedWidth(50)
        start_settings_layout.addWidget(self.channel_edit, 3, 1)
        self.send_commandJV_btn = QtGui.QPushButton(u'ок')
        start_settings_layout.addWidget(self.send_commandJV_btn, 3, 2)
        self.send_commandJV_btn.clicked.connect(self.send_jv_command_clicked)

        self.save_settings_btn = QtGui.QPushButton(u'Сохранить')
        self.default_settings_btn = QtGui.QPushButton(u'Сбросить')
        self.clear_btn = QtGui.QPushButton(u'Очистить')
        self.clear_btn.clicked.connect(self.clear_btn_clicked)
        self.save_settings_btn.setFixedWidth(70)
        self.default_settings_btn.setFixedWidth(70)
        start_settings_layout.addWidget(self.save_settings_btn, 4, 0)
        start_settings_layout.addWidget(self.default_settings_btn, 4, 2)
        start_settings_layout.addWidget(self.clear_btn, 5, 0)
        self.save_settings_btn.clicked.connect(self.save_settings_btn_clicked)
        self.default_settings_btn.clicked.connect(self.default_settings_btn_clicked)
        #list_commands_start_settings = QtGui.QWidget()
        #start_settings_layout.addWidget(list_commands_start_settings)

        list_parameters = QtGui.QWidget()
        options_layout.addWidget(list_parameters)
        options_layout.addWidget(QtGui.QWidget())
        list_parameters.setLayout(self.grid)
        description_status_layout = QtGui.QVBoxLayout(description_status_connect)
        status_connect = QtGui.QGroupBox(u'Статус подключения')
        info_source_address = QtGui.QGroupBox(u'MAC-адрес подключенного модуля')
        info_destination_address = QtGui.QGroupBox()
        description_status_layout.addWidget(status_connect)
        description_status_layout.addWidget(info_source_address, QtCore.Qt.AlignCenter)
        description_status_layout.addWidget(info_destination_address, QtCore.Qt.AlignCenter)
        self.status_connect_layout = QtGui.QHBoxLayout()
        self.info_source_address_layout = QtGui.QGridLayout(info_source_address)
        self.info_destination_address_layout = QtGui.QGridLayout(info_destination_address)
        self.parameters_connecting()

        """Индикатор подключения"""
        self.conn_off_icon = QtGui.QPixmap('images/red_led.png')
        self.conn_on_icon = QtGui.QPixmap('images/green_led.png')
        self.labelForIcon = QtGui.QLabel()
        self.Icon_lbl = QtGui.QLabel(self.module_type)
        self.status_connect_layout.addWidget(self.Icon_lbl)
        self.labelForIcon.setPixmap(self.conn_off_icon)
        self.status_connect_layout.addWidget(self.labelForIcon)
        status_connect.setLayout(self.status_connect_layout)

    """ Парамметры подключения, для 1-ой вкладки"""
    def parameters_connecting(self):
        com_lbl = QtGui.QLabel(u'COM порт')
        com_list = QtGui.QComboBox()
        com_list.setFixedWidth(80)
        com_list.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        com_list.setCurrentIndex(3)
        self.grid.addWidget(com_list, 1, 1)
        speed_lbl = QtGui.QLabel(u'Скорость передачи')
        speed_list = QtGui.QComboBox()
        speed_list.setFixedWidth(80)
        speed_list.addItems(["9600", "115200"])
        self.grid.addWidget(speed_list, 2, 1)
        self.connecting_btn = QtGui.QPushButton(u"Открыть порт")
        self.connecting_btn.setFixedWidth(90)
        self.close_port_btn = QtGui.QPushButton(u'Закрыть порт')
        self.close_port_btn.setFixedWidth(90)
        self.grid.addWidget(self.close_port_btn, 7, 1)
        self.grid.addWidget(self.connecting_btn, 7, 0)
        self.grid.addWidget(com_lbl, 1, 0)
        self.grid.addWidget(speed_lbl, 2, 0)
        com_lbl.resize(500, com_lbl.height())
        self.connPrefFiels = [com_list, speed_list]

    """ Вкладка управление """
    def tab_control(self):
        tab_control_layout = QtGui.QHBoxLayout(self.tab2)
        send_commands = QtGui.QGroupBox(u'Отправка команды')
        list_commands = QtGui.QGroupBox(u'Список доступных команд')
        tab_control_layout.addWidget(send_commands)
        tab_control_layout.addWidget(list_commands, QtCore.Qt.AlignLeft)
        send_commands_layout = QtGui.QGridLayout(send_commands)
        self.command_edit = QtGui.QLineEdit()
        self.list_commands_layout = QtGui.QHBoxLayout(list_commands)
        self.list_all_commands()
        type_commands_lbl = QtGui.QLabel(u'Тип команды')
        send_commands_layout.addWidget(type_commands_lbl, 1, 0)
        self.list_type_commands = QtGui.QComboBox()
        self.list_type_commands.setFixedWidth(80)
        self.list_type_commands.addItems(["at", "remote_at"])
        send_commands_layout.addWidget(self.list_type_commands, 1, 1)
        command_lbl = QtGui.QLabel(u'Команда')
        send_commands_layout.addWidget(command_lbl, 2, 0)
        self.command_edit.setFixedWidth(80)
        send_commands_layout.addWidget(self.command_edit, 2, 1)
        parameter_lbl = QtGui.QLabel(u'Параметры')
        send_commands_layout.addWidget(parameter_lbl, 3, 0)
        self.comm_parameter_edit = QtGui.QLineEdit()
        self.comm_parameter_edit.setFixedWidth(80)
        send_commands_layout.addWidget(self.comm_parameter_edit, 3, 1)
        self.addr_dest_lbl = QtGui.QLabel(u'MAC-адрес назначения')
        self.addr_dest_edit = QtGui.QLineEdit()
        self.addr_dest_edit.setToolTip(u'Указывать в случае remote_at')
        self.addr_dest_edit.setFixedWidth(80)

        send_commands_layout.addWidget(self.addr_dest_lbl, 4, 0)
        send_commands_layout.addWidget(self.addr_dest_edit, 4, 1)



        """ Автодополнения команд начало """
        model = QtGui.QStringListModel()
        model.setStringList(commands)
        completer = QtGui.QCompleter()
        completer.setCaseSensitivity(0)
        completer.setModel(model)
        self.command_edit.setCompleter(completer)
        """ Автодополнения команд конец """

        self.send_command_btn = QtGui.QPushButton(u'Отправить')
        self.test_label_edit = QtGui.QLineEdit()
        #send_commands_layout.addWidget(self.test_label_edit, 8, 0)
        self.send_test_btn = QtGui.QPushButton(u'тест')
        #send_commands_layout.addWidget(self.send_test_btn, 7, 0)
        #send_commands_layout.addWidget(self.send_command_btn, 5, 0)
        self.send_command_btn.clicked.connect(self.send_btn_clicked)
        #self.send_test_btn.clicked.connect(self.send_btn_test)

    """ Список доступных команд """
    def list_all_commands(self):
        self.tab2_all_commands_widget = AllCommandsListWidget(self.command_edit)
        self.list_commands_layout.addWidget(self.tab2_all_commands_widget)

    """Вкладка структура сети)"""
    def tab_network_structure(self):
        self.update_network_btn = QtGui.QPushButton(u"Обновить")
        self.update_network_btn.setFixedSize(60, 40)
        self.scene = QtGui.QGraphicsScene(parent=self.tab3)
        self.scene_view = QtGui.QGraphicsView(self.scene)
        self.scene_view_widget = QtGui.QVBoxLayout(self.tab3)
        self.scene_view_widget.addWidget(self.update_network_btn)
        self.scene_view_widget.addWidget(self.scene_view)
        self.connect(self.connecting_btn, QtCore.SIGNAL("clicked()"), lambda fields=self.connPrefFiels: self.readPrefs(fields))
        self.update_network_btn.clicked.connect(self.on_update_network_btn_clicked)
        self.tabWidget.currentChanged.connect(self.hide_log)

    """ Логирование """
    def options_log(self):
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

    def hide_log(self, ss):
        if ss == 2:
            self.logWidget.widget.setVisible(False)
        else:
            self.logWidget.widget.setVisible(True)

    """Функция индикации подключения и вывод версии прошивки"""
    def connectionIndicate(self, firmware):
        self.Icon_lbl.setText(module_type_dict[str(firmware[:2])])
        firm_id = str(firmware[:2])
        if firm_id == '21':
            self.coord = QtGui.QPixmap('images/zc.png')
            self.coor_item = QtGui.QGraphicsPixmapItem(self.coord, scene=self.scene)
            self.coor_item.setOffset(100, 300)
        self.labelForIcon.setPixmap(self.conn_on_icon)

    """функция считавания значений и подключения модуля"""
    def readPrefs(self, fields):
        self.connPrefs = []
        for i in fields:
            item = i.itemText(i.currentIndex())
            self.connPrefs.append(item)

        # отправляем в поток параметры подключения
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
        """
        self.connect(self.coor, QtCore.SIGNAL('SendOperatingChannel(QString)'),
                     self.operating_channel_indicate, QtCore.Qt.QueuedConnection)
                     """
        self.connect(self.coor, QtCore.SIGNAL('SendDestinationAddressHigh(QString)'),
                     self.dh_info_connecting_dev, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('SendDestinationAddressLow(QString)'),
                     self.dl_info_connecting_dev, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('SerialNumberHigh(QString)'),
                     self.sh_info_connecting_dev, QtCore.Qt.QueuedConnection)
        self.connect(self.coor, QtCore.SIGNAL('SerialNumberLow(QString)'),
                     self.sl_info_connecting_dev, QtCore.Qt.QueuedConnection)
        self.coor.start()
        self.connect(self.close_port_btn, QtCore.SIGNAL("clicked()"), self.close_port_info)

    "Функция закрытия com порта"
    def close_port_info(self):
        self.coor.closePort()
        self.labelForIcon.setPixmap(self.conn_off_icon)

    def send_btn_clicked(self):
        _type_command = self.list_type_commands.currentText()
        _frame_id = self.coor.current_frame_id
        _dest_addr = self.addr_dest_edit.text()
        _command = self.command_edit.text()
        _parameter = self.comm_parameter_edit.text()
        self.logMessage(_command)

        if _type_command == 'at':
            self.coor.sendATCommand(_type_command, _frame_id, _command, _parameter)
        elif _type_command == 'remote_at':
            self.coor.sendRemoteATCommand(_type_command, _frame_id, _dest_addr, _command, _parameter)
        #elif _type_command == 'remote_at':
            #self.coor.sendRemoteCommand(_type_command, _dest_addr, _frame_id, _command, _parameter)

    def send_remote_at_clicked(self):
        #_type_command5 = self.list_type_commands.currentText()
        #_dest_address = self.addr_dest_edit.text()
        #_frame_id1 = self.coor.current_frame_id
        _command2 = self.command_edit.text()
        #_parameter3 = self.comm_parameter_edit.text()
        self.logMessage(_command2)
        self.coor.sendRemoteCommand(_command2)

    def send_id_command_clicked(self):
        _parameter_id = self.pan_id_edit.text()
        self.logMessage(_parameter_id)
        self.coor.sendIDCommand(_parameter_id)

    def send_ni_command_clicked(self):
        _parameter_ni = self.name_edit.text()
        self.logMessage(_parameter_ni)
        self.coor.sendNICommand(_parameter_ni)

    def send_jv_command_clicked(self):
        _parameter_ni = self.channel_edit.text()
        self.logMessage(_parameter_ni)
        self.coor.sendJVCommand(_parameter_ni)

    def send_btn_test(self):
        _frame_id_remote = self.coor.current_frame_id
        dest_address_v1 = self.test_label_edit.text()
        command_v1_test = self.command_edit.text()
        parameter_v1_test = self.comm_parameter_edit.text()
        self.coor.sendTestCommand(_frame_id_remote,dest_address_v1, command_v1_test, parameter_v1_test)

    def on_update_network_btn_clicked(self):
        self.coor.sendNDCommand()

    def save_settings_btn_clicked(self):
        self.coor.sendWRCommand()

    def default_settings_btn_clicked(self):
        self.coor.sendRECommand()
    """
    def operating_channel_indicate(self, channel):
        operating_channel_name_lbl = QtGui.QLabel(u"Рабочий канал: ")
        operating_channel_lbl = QtGui.QLabel()
        self.status_connect_layout.addWidget(operating_channel_name_lbl)
        self.status_connect_layout.addWidget(operating_channel_lbl)
        operating_channel_lbl.setText(channel)
    """

    def dh_info_connecting_dev(self, DH):
        info_dh_lbl_name = QtGui.QLabel(u"Серийный номер(верхний): ")
        info_dh_lbl = QtGui.QLabel()
        self.info_destination_address_layout.addWidget(info_dh_lbl_name, 1, 0)
        self.info_destination_address_layout.addWidget(info_dh_lbl, 1, 1)
        info_dh_lbl.setText(DH)

    def dl_info_connecting_dev(self, DL):
        info_dl_lbl_name = QtGui.QLabel(u"Серийный номер(нижний): ")
        info_dl_lbl = QtGui.QLabel()
        self.info_destination_address_layout.addWidget(info_dl_lbl_name, 2, 0)
        self.info_destination_address_layout.addWidget(info_dl_lbl, 2, 1)
        info_dl_lbl.setText(DL)

    def sh_info_connecting_dev(self, SH):
        info_dh_lbl_name = QtGui.QLabel(u"Серийный номер(верхний): ")
        info_dh_lbl = QtGui.QLabel()
        self.info_source_address_layout.addWidget(info_dh_lbl_name, 1, 0)
        self.info_source_address_layout.addWidget(info_dh_lbl, 1, 1)
        info_dh_lbl.setText(SH)

    def sl_info_connecting_dev(self, SL):
        info_dl_lbl_name = QtGui.QLabel(u"Серийный номер(нижний): ")
        info_dl_lbl = QtGui.QLabel()
        self.info_source_address_layout.addWidget(info_dl_lbl_name, 2, 0)
        self.info_source_address_layout.addWidget(info_dl_lbl, 2, 1)
        info_dl_lbl.setText(SL)

    def update_network_structure(self, response):
        x = random.randrange(50, 800)
        y = random.randrange(50, 600)
        response_dict = json.loads(str(response))
        addr = response_dict['source_addr_long']
        self.coor.sendDataToForm(addr)
        if addr in self.graphics_scene_items.values():
            return
        addr_item = QtGui.QGraphicsTextItem(addr, parent=None, scene=self.scene)
        item = QtGui.QGraphicsPixmapItem(scene=self.scene)
        self.graphics_scene_items[item] = addr
        if response_dict["device_type"] == "01":
            item.setPixmap(QtGui.QPixmap('images/zr.png'))
        if response_dict["device_type"] == "02":
            item.setPixmap(QtGui.QPixmap('images/ze.png'))
        item.setOffset(x, y)
        addr_item.setPos(x + 40, y + 50)

    def logMessage(self, text):
        logging.debug(text)

    def clear_btn_clicked(self):
        self.pan_id_edit.clear()
        self.name_edit.clear()
        self.channel_edit.clear()

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu()
        settings_action = menu.addAction(u"Настройки")
        action = menu.exec_(event.globalPos())
        if action == settings_action:
            self.on_show()

    def on_show(self):
        win = ModalWind(self)
        win.show()

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
    bl = mainWindow()
    bl.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
