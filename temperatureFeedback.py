from daqmx_channel import daqmx_channel_in
from T255Controller import T255Controller
import time
import logging
logging.basicConfig(logLevel = logging.DEBUG)
import threading
import numpy as np
import sys


class CircularArray:
    def __init__(self, length):
        """" Create a circular array of length length """
        self.length = length

        self._array = np.array(int(self.length)*[None])
        self._last_key = 0

    def __setitem__(self, key, item):
        
        modified_key = key % self.length
        self._last_key = modified_key
        self._array[modified_key] = item

    def __getitem__(self, key):
        if key < 0:
            key = self._last_key + key

        modified_key = key % self.length
        return self._array[modified_key]

    def toArray(self):
        return self._array

    def __str__(self):
        return self._array.__str__()


class feedbackLoop(threading.Thread):

#    min_signal = 1.5 #v. The minimum value before regulating
#    max_signal = 4.7 #v. The maximum value of the monitor before regulating
    min_signal = 2.2
    max_signal = 4.0
    length_signals = 200 # the number of last signals to keep
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        try:
            self.PID_output = daqmx_channel_in(num_samples = 10, channel=0)
        except:
            print "Could not connect to daqmx. Aborting"
            sys.exit(1)

        try:
            self.cooler = T255Controller()
        except: 
            print "Could not connect to chiller. Aborting"
            sys.exit(1)

        self.logger = logging.getLogger('feedbackLoop')
        self.logger.setLevel(logging.INFO)

        self.active = True
        self.t0 = time.time()
        # start assuming that the PID is within bounds
        self.PID_within_bounds = True

        self.signal_history = CircularArray(self.length_signals)
        self.time_history = CircularArray(self.length_signals)


    def run(self):
        iteration = -1
        while True:
            if self.active:

                iteration +=1
                self.signal = self.PID_output.read_voltage()
                self.signal_history[iteration] = self.signal.mean()
                self.time_history[iteration] = time.time()

                # check that the device is in lock
                if self.lockbox_status() == 1:
                    # regulate!
                    self.performFeedback(simulate=False)
                else:
                    self.t0 = time.time()
                    self.performFeedback(simulate=True)
#                time.sleep(5)
                time.sleep(.15)
            else:
                time.sleep(0.1)



    def lockbox_status(self):
        """"Take a look at the last signal (self.signal) and decide wether or not the lockbox is locked. 
        return:
            0 Lockbox is not locking
            1 Lockbox is locking
            2 Lockbox is out of lock
        """
        std = self.signal.std()

        if std > 0.3:
            self.logger.debug('Lockbox is out of lock')
            return 2
        elif std < 0.005:
            self.logger.debug('Lockbox is Not locking')
            return 0
        else:
            self.logger.debug('Lockbox is locking')
            return 1

    def performFeedback(self, simulate=False):
#        print "signal: ", self.signal.mean()
#        print "Last signal: " , self.signal_history[-1]

        mean = self.signal.mean()

        # 1. Check if the signal is within the bounds:

        if simulate:
            return

        if mean < self.min_signal:

            self.t0 = time.time()
            self.logger.info('Lower bound')
            if self.PID_within_bounds:
                self.logger.info('Raise baseplate temperature')
                if not self.cooler.raise_temperature():
                    self.logger.error("Could not raise temperature")

                self.PID_within_bounds = False
            
        elif mean > self.max_signal:
            self.logger.info('Upper bound')
            self.t0 = time.time()

            if self.PID_within_bounds:
                self.logger.info('Lower baseplate temperature')
                if not self.cooler.lower_temperature():
                    self.logger.error("Could not lower temperature")
                self.PID_within_bounds = False
        else:
            # set PID within bounds if last 20 seconds were within bounds
            
            if time.time() - self.t0 > 20:
                if not self.PID_within_bounds:
                    self.logger.info('Set PID_within_bounds to True')
                self.PID_within_bounds = True


    def __del__(self):
        print "Cleaning up!" 
        self.PID_output.cleanup()


if __name__ == '__main__':

    print "Starting feedback loop"
    fl = feedbackLoop()
    print "Set up feedbackloop"
    fl.active = False
    fl.start()
    x = raw_input('press any key to abort')
    del feedbackLoop
    time.sleep(1)
        
        
