class XbeeModule:
    """
    Будем создавать экземпляр этого класса каждый раз, когда появляется новое устройство в сети (после ND)
    """
    def __init__(self, address):
        self.address = address
        self.type = None
        self.DL = None
        self.DH = None
        self.firmware = None
        self.directly_connected = None

    def set_property(self, prop, value):
        """функция для настройки модуля"""
        # TODO Добавить необходимые для настройки свойства, например:
        if prop == "type":
            self.type = value
        elif prop == "DL":
            self.DL = value
        elif prop == "DH":
            self.DH = value
