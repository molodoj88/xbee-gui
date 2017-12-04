# -*- coding: utf-8 -*-

"""
Здесь будут храниться все необходимые AT команды для
конфигурации и связи с модулями xbee
"""

from xbee import XBee
import json
import os

with open("CommandDescriptions.json") as jsonFile:
    descriptions = json.load(jsonFile)


class Command:
    def __init__(self, command, nodeType, parameterRange, defaultValue, desc=descriptions):
        """
        Basic command representation
        :param command: String, AT command
        :param nodeType: String, Node types that support the command: C=Coordinator, R=Router, E=End Device,
        for ex.: "CRE", "RE", "C"
        :param parameterRange: String
        :param defaultValue: string, byte or integer
        :param desc: JSON object with command descriptions
        """
        self.command = command
        self.nodeType = nodeType
        self.parameterRange = parameterRange
        self.defaultValue = defaultValue.encode('utf-8')
        self.desc = desc

    def __str__(self):
        return "Command: {}\n{}\nNode types: {}\nParameter range: {}\nDefault value: {}".format(
            self.command,
            self.get_description(),
            self.nodeType,
            self.parameterRange,
            self.defaultValue
        )

    def get_description(self):
        """
        Get description of command (if exist)
        :return: string with description or 'No description'
        """
        try:
            d = self.desc[self.command]
        except KeyError:
            return 'No description'
        else:
            return d

    def send(self):
        pass


class CAddressing:
    DESTINATION_ADDRESS_HIGH = Command("DH", "CRE", "0-0xFFFFFFFF", "0")
    DESTINATION_ADDRESS_LOW = Command("DL", "CRE", "0-0xFFFFFFFF", "0")
    NETWORK_ADDRESS_16_BIT = Command("MY", "CRE", "0-0xFFFE", "0xFFFE")
    NETWORK_ADDRESS_PARENT_16_BIT = Command("MP", "E", "0-0xFFFE", "0xFFFE")
    SERIAL_NUMBER_HIGH = Command("SH", "CRE", "0 - 0xFFFFFFFF", "factory-set")
    SERIAL_NUMBER_LOW = Command("SL", "CRE", "0 - 0xFFFFFFFF", "factory-set")
    NODE_IDENTIFIER = Command("NI", "CRE", "", "")
    SOURCE_ENDPOINT = Command("SE", "CRE", "0 - 0xFF", "0xE8")
    DESTINATION_ENDPOINT = Command("DE", "CRE", "0 - 0xFF", "0xE8")
    CLUSTER_IDENTIFIER = Command("CI", "CRE", "0 - 0xFFFF", "0x11")
    DEVICE_TYPE_IDENTIFIER = Command("DD", "CRE", "0 - 0xFFFFFFFF", "0x30000")


class CNetworking:
    OPERATING_CHANNEL = Command("CH", "CRE", "0, 0x0B - 0x18", "read-only")
    FORCE_DISASSOCIATION = Command("DA", "CRE", "", "")
    EXTENDED_PAN_ID = Command("ID", "CRE", "0-0xFFFFFFFFFFFFFFFF", "0")
    OPERATING_EXTENDED_PAN_ID = Command("OP", "CRE", "0x01-0xFFFFFFFFFFFFFFFF", "read-only")
    MAXIMUM_UNICAST_HOPS = Command("NH", "CRE", "0 - 0xFF", "0x1E")
    BROADCAST_HOPS = Command("BH", "CRE", "0 - 0x0F", "0")
    OPERATING_16_BIT_PAN_ID = Command("OI", "CRE", "0 - 0xFFFF", "read-only")
    NODE_DISCOVERY_TIMEOUT = Command("NT", "CRE", "0x20 - 0xFF [x 100 msec]", "0x3C (60d)")
    NODE_DISCOVER = Command("ND", "CRE", "optional 20-Byte NI or MY value", "")
    DESTINATION_NODE = Command("DN", "CRE", "up to 20-Byte printable ASCII string", "")
    SCAN_CHANNELS = Command("SC", "CRE", "1 - 0xFFFF", "0x1FFE")
    SCAN_DURATION = Command("SD", "CRE", "0 - 7 [exponent]", "3")
    NODE_JOIN_TIME = Command("NJ", "CRE", "0 - 0xFF", "0xFF")
    CHANNEL_VERIFICATION = Command("JV", "R", "0 - Channel verification disabled 1 - Channel verification enabled", "0")
    NETWORK_WATCHDOG_TIMEOUT = Command("NW", "R", "0 - 0x64FF", "0(disabled)")
    JOIN_NOTIFICATION = Command("JN", "RE", "0 - 1", "0")
    AGGREGATE_ROUTING_NOTIFICATION = Command("AR", "CR", "0 - 0xFF", "0xFF")

        
class CSecurity:
    ENCRYPTION_ENABLE = Command("EE", "CRE", "0 - Encryption disabled 1 - Encryption enabled", "0")
    ENCRYPTION_OPTIONS = Command("EO", "CRE", "0 - 0xFF", "")
    NETWORK_ENCRYPTION_KEY = Command("NK", "C", "128-bit value", "0")
    LINK_KEY = Command("KY", "CRE", "128-bit value", "0")


class CRFInterfacing:
    POWER_LEVEL = Command("PL", "CRE", "0-4", "4")
    POWER_MODE = Command("PM", "CRE", "0-1", "1")
    RECEIVED_SIGNAL_STRENGTH = Command("DB", "CRE", "0x 1A - 0x5C", "")
    PEAK_POWER = Command("PP", "CRE", "0x0-0x12", "read-only")


class CSerialInterfacing:
    API_ENABLE = Command("AP", "CRE", "1-2", "1")
    API_OPTIONS = Command("AO", "CRE", "0-1", "0")
    INTERFACE_DATA_RATE = Command("BD", "CRE", "0-7", "3")
    SERIAL_PARITY = Command("NB", "CRE", "0-3", "0")
    PACKETIZATION_TIMEOUT = Command("RO", "CRE", "0 - 0xFF", "3")
    
    
class CDiagnostics:
    FIRMWARE_VERSION = Command("VR", "CRE", "0 - 0xFFFF", "")
    HARDWARE_VERSION = Command("HV", "CRE", "0 - 0xFFFF", "")
    ASSOCIATION_INDICATION = Command("AI", "CRE", "0 - 0xFF[read-only]", "")


class CSleep:
    SLEEP_MODE = Command("SM", "RE", "0-1, 4", "0")
    NUMBER_OF_SLEEP_PERIODS = Command("SN", "CRE", "1 - 0xFFFF", "1")
    SLEEP_PERIOD = Command("SP", "CRE", "0x20 - 0xAF0", "0x7D0")
    TIME_BEFORE_SLEEP = Command("ST", "RE", "1 - 0xFFFE", "0x1388(5sec)")
    POLLING_RATE = Command("PO", "E", "0 - 0x3E8", "0x00 (100msec)")


class CExecution:
    APPLY_CHANGES = Command("AC", "CRE", "", "")
    WRITE = Command("WR", "CRE", "", "")
    RESTORE_DEFAULTS = Command("RE", "CRE", "", "")
    SOFTWARE_RESET = Command("FR", "CRE", "", "")
    NETWORK_RESET = Command("NR", "CRE", "0-1", "")
    SLEEP_IMMEDIATELY = Command("SI", "E", "", "")

ALL_CLASSES = [CAddressing, CExecution, CNetworking, CDiagnostics,
               CSecurity, CSleep, CSerialInterfacing, CRFInterfacing]

if __name__ == "__main__":
    # Для теста
    print CAddressing.__name__
    pass