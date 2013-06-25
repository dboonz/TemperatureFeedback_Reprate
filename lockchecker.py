from daqmx_channel import *
import numpy as np
import time



with daqmx_channel_in(num_samples = 10, channel=0) as PID_output:
        while True:
            PID_output_sig = PID_output.read_voltage()

            std = PID_output_sig.std()

            if std > 0.3:
                print "Out of lock: std " , data.std()
            elif std < 0.005:
                print "Not locking"
            else:
                print "In lock"
            


            time.sleep(1)


