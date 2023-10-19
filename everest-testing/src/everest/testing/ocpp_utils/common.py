from enum import Enum


class OCPPVersion(str, Enum):
    ocpp16 = "ocpp1.6"
    ocpp201 = "ocpp2.0.1"
