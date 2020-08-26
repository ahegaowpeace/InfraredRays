import configparser
import argparse
import sys
 
 
FILENAME_CONFIG = "daikin.conf"
FILENAME_COMMAND = "daikin.txt"
BIT_0 = "0x00,0x12,0x00,0x12,"
BIT_1 = "0x00,0x12,0x00,0x31,"
BIT_LEADER = "0x00,0x86,0x00,0x41,"
BIT_STOP1 = "0x00,0x12,0x03,0xc1,"
BIT_STOP2 = "0x00,0x13,0x05,0x22,"
BIT_STOP3 = "0x00,0x12,0x1e,0x0d"
BYTES_FRAME1 = [ 0x11, 0xda, 0x27, 0x00, 0xc5, 0x00, 0x00, 0xd7 ]
BYTES_FRAME2 = [ 0x11, 0xda, 0x27, 0x00, 0x42, 0x00, 0x00, 0x54 ]
 
 
def load_config(config, filename, section):
    config.read(filename)
 
    options = {}
    options["power"] = config.get(section, "power", fallback="on")
    options["fan"] = config.getint(section, "fan", fallback=0)
    options["swing"] = config.get(section, "swing", fallback="on")
    options["temperature"] = config.getint(section, "temperature", fallback=30)
    options["mode"] = config.get(section, "mode", fallback="cold")
    options["delay"] = config.getint(section, "delay", fallback=0)
 
    return options
 
 
def save_config(config, filename, section, options):
 
    if (not config.has_section(section)):
        config.add_section(section)
 
    for k, v in options.items():
        config.set(section, k, str(v))
 
    with open("./daikin.conf", "w") as f:
        config.write(f)
 
    return
 
 
def merge_config(config1, config2):
    for k, v in config2.items():
        if (v != None):
            config1[k] = v;
 
    return config1
 
 
def get_parameter(parser):
    parser.add_argument('-p', '--power', type=str, help='on|off')
    parser.add_argument('-f', '--fan', type=int, help='0..5')
    parser.add_argument('-s', '--swing', type=str, help='on|off')
    parser.add_argument('-t', '--temperature', type=int, help='18..30')
    parser.add_argument('-m', '--mode', type=str, help='cold|heat')
    parser.add_argument('-d', '--delay', type=int, help='0..5 <0:offtimer >0:ontimer')
    args = parser.parse_args()
 
    return vars(args)
 
 
def build_mode(mode):
    bits = ""
    if (mode == "cold"):
        bits = "0011"
    elif (mode == "heat"):
        bits = "0100"
    else:
        raise ValueError("invalid value for mode: '{}'".format(mode))
 
    return bits;
 
 
def build_timer(delay):
    bits = ""
    if (delay == 0):
        bits = "00"
    elif (delay > 0):
        bits = "01"
    elif (delay < 0):
        bits = "10"
    else:
        raise ValueError("invalid value for delay: '{}'".format(delay))
 
    return bits
 
 
def build_power(power):
    bits = ""
    if (power == "on"):
        bits = "1"
    elif (power == "off"):
        bits = "0"
    else:
        raise ValueError("invalid value for power: '{}'".format(power))
 
    return bits
 
 
def build_fan(fan):
    bits = ""
    if (fan == 0):
        bits = "1011"
    elif (fan >= 1 and fan <= 5):
        bits = format(fan + 2, "04b")
    else:
        raise ValueError("invalid value for fan: '{}'".format(fan))
 
    return bits
 
 
def build_swing(swing):
    bits = ""
    if (swing == "on"):
        bits = "1111"
    elif (swing == "off"):
        bits = "0000"
    else:
        raise ValueError("invalid value for swing: '{}'".format(swing))
 
    return bits
 
 
def build_temperature(temperature):
    bits = ""
    if (temperature >= 18 and temperature <= 30):
        bits = format(options["temperature"] * 2, "08b")
    else:
        raise ValueError("invalid value for temperature: '{}'".format(temperature))
 
    return bits
 
 
def build_delay1(delay):
    bits = ""
    if (delay == 0):
        bits = "00000000"    
    elif (delay > 0):
        minutes = delay * 60
        bits = format(minutes & 0xff, "08b")
    elif (delay < 0):
        bits = "00000000"    
    else:
        raise ValueError("invalid value for delay: '{}'".format(delay))
 
    return bits
 
 
def build_delay2(delay):
    bits = ""
    if (delay == 0):
        bits = "00000110"
    elif (delay > 0):
        minutes = delay * 60
        bits = format((minutes >> 8) & 0xff, "08b")
    elif (delay < 0):
        minutes = -1 * delay * 60
        if (minutes > 0xff):
            bits = format(minutes & 0xff, "08b")
        else:
            bits = format(0x06 | ((minutes & 0x0f) << 4), "08b")
    else:
        raise ValueError("invalid value for delay: '{}'".format(delay))
 
    return bits
 
 
def build_delay3(delay):
    bits = ""
    if (delay == 0):
        bits = "01100000"
    elif (delay > 0):
        bits = "01100000"
    elif (delay < 0):
        minutes = -1 * delay * 60
        if (minutes > 0xff):
            bits = format(minutes >> 8, "08b")
        else:
            bits = format(minutes >> 4, "08b")
    else:
        raise ValueError("invalid value for delay: '{}'".format(delay))
 
    return bits
 
 
def build_command(options):
 
    commands = []
 
    hexcmd = [];
    hexcmd.append(0x11)
    hexcmd.append(0xDA)
    hexcmd.append(0x27)
    hexcmd.append(0x00)
    hexcmd.append(0x00)
    hexcmd.append(int(build_mode(options["mode"]) + "1" + build_timer(options["delay"]) + build_power(options["power"]), 2))
    hexcmd.append(int(build_temperature(options["temperature"]), 2))
    hexcmd.append(0x00) 
    hexcmd.append(int(build_fan(options["fan"]) + build_swing(options["swing"]), 2))
    hexcmd.append(0x00) 
    hexcmd.append(int(build_delay1(options["delay"]), 2))
    hexcmd.append(int(build_delay2(options["delay"]), 2))
    hexcmd.append(int(build_delay3(options["delay"]), 2))
    hexcmd.append(0x00)
    hexcmd.append(0x00)
    hexcmd.append(0xC1) 
    hexcmd.append(0x00)
    hexcmd.append(0x00)
    hexcmd.append(calc_checksum(hexcmd))
 
    return hexcmd;
 
 
def calc_checksum(command):
    total = 0
    for item in command:
        total += item 
    checksum = total & 0xff
 
    return checksum
 
 
def dump_byte(byte):
    buf = ""
    for i in range(8):
        if (byte & 0x01 == 1):
            buf += BIT_1
        else:
            buf += BIT_0
        byte = byte >> 1
 
    return buf
 
 
def dump_command(options):
    buf = ""
 
    # bit0 x 5
    buf += BIT_0 + BIT_0 + BIT_0 + BIT_0 + BIT_0
    buf += BIT_STOP1
 
    # frame1
    buf += BIT_LEADER
    for item in BYTES_FRAME1:
        buf += dump_byte(item)
    buf += BIT_STOP2
 
    # frame2
    buf += BIT_LEADER
    for item in BYTES_FRAME2:
        buf += dump_byte(item)
    buf += BIT_STOP2
 
    # frame3
    command = build_command(options)
    buf += BIT_LEADER
    for item in command:
        buf += dump_byte(item)
    buf += BIT_STOP3
 
    return buf
 
 
if __name__ == "__main__":
    config = configparser.SafeConfigParser()
    parser = argparse.ArgumentParser()
 
    options = load_config(config, FILENAME_CONFIG, "default")
    pars = get_parameter(parser)
    merge_config(options, pars)
 
    buf = dump_command(options)
    with open(FILENAME_COMMAND, "w") as f:
        f.write(buf)
 
    save_config(config, FILENAME_CONFIG, "default", options)
