"""State mappings for Lambda WP sensors."""

# Heat Pump States
HP_ERROR_STATE = {
    0: "NONE",
    1: "MESSAGE",
    2: "WARNING",
    3: "ALARM",
    4: "FAULT",
}

HP_STATE = {
    0: "INIT",
    1: "REFERENCE",
    2: "RESTART-BLOCK",
    3: "READY",
    4: "START PUMPS",
    5: "START COMPRESSOR",
    6: "PRE-REGULATION",
    7: "REGULATION",
    8: "Not Used",
    9: "COOLING",
    10: "DEFROSTING",
    20: "STOPPING",
    30: "FAULT-LOCK",
    31: "ALARM-BLOCK",
    40: "ERROR-RESET",
}

HP_RELAIS_STATE_2ND_HEATING_STAGE = {
    0: "Off",
    1: "On",
}

HP_OPERATING_STATE = {
    0: "STBY",
    1: "CH",
    2: "DHW",
    3: "CC",
    4: "CIRCULATE",
    5: "DEFROST",
    6: "OFF",
    7: "FROST",
    8: "STBY-FROST",
    9: "Not used",
    10: "SUMMER",
    11: "HOLIDAY",
    12: "ERROR",
    13: "WARNING",
    14: "INFO-MESSAGE",
    15: "TIME-BLOCK",
    16: "RELEASE-BLOCK",
    17: "MINTEMP-BLOCK",
    18: "FIRMWARE-DOWNLOAD",
}

HP_REQUEST_TYPE = {
    0: "NO REQUEST",
    1: "FLOW PUMP CIRCULATION",
    2: "CENTRAL HEATING",
    3: "CENTRAL COOLING",
    4: "DOMESTIC HOT WATER",
}

# Boiler States
BOIL_CIRCULATION_PUMP_STATE = {
    0: "Off",
    1: "On",
}

BOIL_OPERATING_STATE = {
    0: "STBY",
    1: "DHW",
    2: "LEGIO",
    3: "SUMMER",
    4: "FROST",
    5: "HOLIDAY",
    6: "PRIO-STOP",
    7: "ERROR",
    8: "OFF",
    9: "PROMPT-DHW",
    10: "TRAILING-STOP",
    11: "TEMP-LOCK",
    12: "STBY-FROST",
}

# Heating Circuit States
HC_OPERATING_STATE = {
    0: "HEATING",
    1: "ECO",
    2: "COOLING",
    3: "FLOORDRY",
    4: "FROST",
    5: "MAX-TEMP",
    6: "ERROR",
    7: "SERVICE",
    8: "HOLIDAY",
    9: "CH-SUMMER",
    10: "CC-WINTER",
    11: "PRIO-STOP",
    12: "OFF",
    13: "RELEASE-OFF",
    14: "TIME-OFF",
    15: "STBY",
    16: "STBY-HEATING",
    17: "STBY-ECO",
    18: "STBY-COOLING",
    19: "STBY-FROST",
    20: "STBY-FLOORDRY",
}

HC_OPERATING_MODE = {
    0: "OFF",
    1: "MANUAL",
    2: "AUTOMATIK",
    3: "AUTO-HEATING",
    4: "AUTO-COOLING",
    5: "FROST",
    6: "SUMMER",
    7: "FLOOR-DRY",
    -1: "Unknown",
}

# Buffer States
BUFF_OPERATING_STATE = {
    0: "STBY",
    1: "HEATING",
    2: "COOLING",
    3: "SUMMER",
    4: "FROST",
    5: "HOLIDAY",
    6: "PRIO-STOP",
    7: "ERROR",
    8: "OFF",
    9: "STBY-FROST",
}

BUFF_REQUEST_TYPE = {
    -1: "INVALID REQUEST",
    0: "NO REQUEST",
    1: "FLOW PUMP CIRCULATION",
    2: "CENTRAL HEATING",
    3: "CENTRAL COOLING",
}

# Solar States
SOL_OPERATING_STATE = {
    0: "STBY",
    1: "HEATING",
    2: "ERROR",
    3: "OFF",
}

# Circulation Pump States
MAIN_CIRCULATION_PUMP_STATE = {
    0: "Off",
    1: "On",
    2: "Error",
}

# Ambient States
MAIN_AMBIENT_OPERATING_STATE = {
    0: "OFF",
    1: "AUTOMATIK",
    2: "MANUAL",
    3: "ERROR",
}

# E-Manager States
MAIN_E_MANAGER_OPERATING_STATE = {
    0: "OFF",
    1: "AUTOMATIK",
    2: "MANUAL",
    3: "ERROR",
    4: "OFFLINE",
}
