import serial
import binascii
import ConfigParser
import numpy as np
import time


def hex2Ascii(hexStr):
    """ Convert hex to ascii string """
    asciiStr = ''
    for i in range(len(hexStr)/2):
            asciiStr += binascii.a2b_hex(hexStr[2*i] + hexStr[2*i+1])
    return asciiStr


def ascii2Hex(asciiStr):
        hexStr = ''
        for i in range(len(asciiStr)):
                hexStr += hex(ord(asciiStr[i]))
        return hexStr


class Regulator:
    def __init__(self, *args, **kwargs):
        self.configparser = ConfigParser.SafeConfigParser()
        self.configparser.read('Regulators.ini')

        self.initialize(*args, **kwargs)

    def readIniField(self, optionname):
        """ Read option. Return answer """
        return self.configparser.get(self.section_name, optionname)

    def close(self):
        """ Called upon ending of the program. Put anything in that has to
        be done in the end, for instance closing a serial port """
        print "Closing t255"

    def initialize(self):
        """ Put everything in this method that is needed to initialize the
        device"""
        pass

    def perform_positive_feedback(self):
        pass

    def perform_negative_feedback(self):
        pass

    def get_value(self):
        """ Return the current value of the regulator """
        pass

    def get_set_value(self):
        """ Return the current set value of the regulator """
        pass

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


class T255Controller(Regulator):
    """ T255 temperature controller regulator """

    commands = {
        'read_coolant_temperature': hex2Ascii('2E4937370D'),
        'read_set_temperature': hex2Ascii('2E483041360D')
               }
    def __init__(self, comport = 'COM11'):
        self.comport = comport

        self.lower_temperature_limit = 17.5
        self.higher_temperature_limit = 17.9
        self.temperature_step = 0.1

        self.serial = serial.Serial(port = self.comport, timeout=0.7)
        
   
    def close(self):
        self.serial.close()
    
    def readCoolantTemperature(self):
        """ Return coolant temperature """
        command = self.commands['read_coolant_temperature']
        return float(self.ask(command)[3:8])/100

    def ask(self, command):
        self.write(command)
        return self.readline()

    def readline(self):
        try:
            return self.serial.readline()
        except:
            print "Error reading serial device"
            return ''

    def read(self):
        try:
            return self.serial.read()
        except:
            print "Error reading serial device"
            return ''

    def getSetTemperature(self):
        """ Return set temperature """
        command = self.commands['read_set_temperature']
        #return hex2Ascii(self.ask(command)[1:])
        return float(self.ask(command)[4:8])/10.

    def setTemperature(self, temperature):
        """ Set the temperature to temperature degrees """
        if temperature > self.higher_temperature_limit:
            raise TemperatureLimitException('Higher limit reached')
        elif temperature < self.lower_temperature_limit:
            message = 'Lower Lim: desired T: %.2f' % temperature
            raise TemperatureLimitException(message)

        temp = int(round(10*temperature))
        
        # split up in three parts
        temp10 = str(temp/100%10) # temperature in tens of degrees
        temp1  = str(temp/10%10)  # one degrees
        temp01 = str(temp%10)     # .1 degrees

        # calculate checksum
        checksum_int =  (46 + 77 +  43 + ord(temp10) +  ord(temp1) +  ord(temp01))%256

        set_temperature_command = '.M+' + str(temp) + hex(checksum_int)[2:] + '\r'
        # write command
        self.write(set_temperature_command)
        
        # read new set temperature
        settemp = self.readline()
        try:
            settemp = float(settemp[4:7])/10.
            print "new set temp: %f" % settemp
        except: 
            print "Could not set temp"


    def write(self, command):
        try:
            self.serial.write(command)
        except:
            print "Error writing. "

    def lower_temperature(self):
        try:
            self.setTemperature(self.getSetTemperature()-self.temperature_step)
            return True
        except TemperatureLimitException as e:
            print e
            return False

    def raise_temperature(self):
        try:
            self.setTemperature(self.getSetTemperature()+self.temperature_step)
            return True
        except TemperatureLimitException as e:
            print e
            return False

class TemperatureLimitException(Exception):
    def __init__(self, string):
        self.message = string

    def __str__(self):
        return self.message

if __name__ == '__main__':
    print "connecting T255"
    import time
    t255 = T255Controller()
    print t255.getSetTemperature(), t255.readCoolantTemperature()
    print "trying to lower temperature: ", t255.lower_temperature() and "Success " or "Failed"
    print "trying to lower temperature: ", t255.lower_temperature() and "Success " or "Failed"
    print "trying to raise temperature: ", t255.raise_temperature() and "Success " or "Failed"
    print "trying to raise temperature: ", t255.raise_temperature() and "Success " or "Failed"


