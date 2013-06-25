#!/usr/bin/env python

#################
#
# 2012 Vasco Tenner
#
# Measure voltage using National Instruments USB-6009 or equivalent device
# to numpy.array.
#
# Until now, works for windows only due to no linux support of NI
#
# You can download the driver here: http://www.ni.com/white-paper/6913/en#usb
# or small download: http://joule.ni.com/nidu/cds/view/p/id/2891/lang/en
# You need to create an account first.
#
# Original from http://www.scipy.org/Cookbook/Data_Acquisition_with_NIDAQmx
# This is a near-verbatim translation of the example program
# C:\Program Files\National Instruments\NI-DAQ\Examples\DAQmx ANSI C\
#        Analog In\Measure Voltage\Acq-Int Clk\Acq-IntClk.c

# 2012.10.19 - Create nice class wrapper for easy usage (vasco)

import ctypes
import numpy
import logging
import time  # temporarly
nidaq = ctypes.windll.nicaiu  # load the DLL

##############################
# Setup some typedefs and constants
# to correspond with values in
# C:\Program Files\National Instruments\NI-DAQ\DAQmx ANSI C Dev\i
#  include\NIDAQmx.h
# the typedefs
uint8 = ctypes.c_uint
int32 = ctypes.c_long
uInt32 = ctypes.c_ulong
uInt64 = ctypes.c_ulonglong
float64 = ctypes.c_double
TaskHandle = uInt32
bool32 = ctypes.c_bool
# the constants
DAQmx_Val_Cfg_Default = int32(-1)
DAQmx_Val_RSE = 10083
DAQmx_Val_diff = 10106
DAQmx_Val_Volts = 10348
DAQmx_Val_Voltage = 10322
DAQmx_Val_Rising = 10280
DAQmx_Val_FiniteSamps = 10178
DAQmx_Val_GroupByChannel = 0
DAQmx_Val_OnDemand = 10390  # On Demand
DAQmx_Val_ContSamps = 10123

#*** Values for the Line Grouping parameter of DAQmxCreateDIChan and
# DAQmxCreateDOChan ***
DAQmx_Val_ChanPerLine = 0   # One Channel For Each Line
DAQmx_Val_ChanForAllLines = 1   # One Channel For All Lines
##############################


class daqmx_channel_in:
    """Measure voltage on a channel of a NI-DAQ device, like USB6009

    Example:
    nr_samples = 1000
    nr_rep = 100
    channel1 = daqmx_channel(num_samples=nr_samples)  # ,clockspeed=48*1000)
    data = channel1.read_voltage()
    channel1.cleanup()
    """

    read = int32()
    timeout = 1

    def __init__(self, device=1, channel=0, clockspeed=10000.0, num_samples=10,
                 v_lim=(-10.0, 10.0)):
        """ Initialize channel to measure.

        arguments:
        channel     -- Channel to measure IN1 on VU box means channel 0
        clockspeed  -- set some clockspeed
        num_samples -- number of points to measure
        v_lim       -- (vmin, vmax) lower and upper voltage measurement
                       boudaries
        """
        # Logger
        self.logger = logging.getLogger("daqmx_channel.daqmx_channel_in")

        self._num_samples = num_samples
        # Initialize an analog input channel for voltage measurement
        self.taskHandle = TaskHandle(device * 8 + channel)
        channel = 'Dev%i/ai%i' % (device, channel)

        # Send commands to initialize an analog input channel
        self.CHK(nidaq.DAQmxCreateTask("", ctypes.byref(self.taskHandle)))
        self.CHK(nidaq.DAQmxCreateAIVoltageChan(self.taskHandle, channel,
                                           "",
                                           DAQmx_Val_diff,
                                           float64(v_lim[0]),
                                           float64(v_lim[1]),
                                           DAQmx_Val_Volts, None))

        self.CHK(nidaq.DAQmxCfgSampClkTiming(self.taskHandle, "",
                                        float64(clockspeed),
                                        DAQmx_Val_Rising,
                                        DAQmx_Val_FiniteSamps,
                                        uInt64(self._num_samples)))

    def __enter__(self, *args, **kwargs):
        """for context manager"""
        return self

    def __exit__(self, type, value, traceback):
        """for context manager"""
        self.cleanup()
        return value

    def CHK(self, err):
        """a simple error checking routine"""
        if err < 0:
            buf_size = 100
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('nidaq call failed with error %d: %s' %
                               (err, repr(buf.value)))

    def is_task_done(self):
        result = bool32(False)
        self.CHK(nidaq.DAQmxIsTaskDone(self.taskHandle, result))
        return result

    def wait_until_task_done(self, timeout=False):
        if not timeout:
            timeout = self.timeout
        self.CHK(nidaq.DAQmxWaitUntilTaskDone(self.taskHandle,
                 float64(timeout)))

    def read_voltage(self):
        """Read an array of voltage data points from the channel"""
        data = numpy.zeros((self._num_samples), dtype=numpy.float64)
        self.logger.debug("Start reading")
        self.CHK(nidaq.DAQmxStartTask(self.taskHandle))
        self.CHK(nidaq.DAQmxReadAnalogF64(self.taskHandle,
                                        self._num_samples,
                                        float64(10.0),
                                        DAQmx_Val_GroupByChannel,
                                        data.ctypes.data,
                                        self._num_samples,
                                        ctypes.byref(self.read), None))
        nidaq.DAQmxStopTask(self.taskHandle)
        self.logger.debug("End reading")
        return data

    def cleanup(self):
        """Always cleanup, else DAQ hardware will lock"""
        nidaq.DAQmxClearTask(self.taskHandle)


class daqmx_digital_out():
    """
    Create 1 bit digital out

    Example:
    import time
    ttl = daqmx_digital_out()
    ttl.set_on()
    time.sleep(5)
    ttl.cleanup()

    Warning: contains a bug. This will only work with port0 , and line 0, otherwise it won't.
    """

    def __init__(self, device=1, port=0, line=0):
        assert(port == 0)
        assert(line == 0)
        addr = 'Dev%i/port%i/line0:7' % (device, port)
        self.taskHandle = TaskHandle(device * 8 + port * 8 + line)
        # setup the DAQ hardware
        self.CHK(nidaq.DAQmxCreateTask("",
                          ctypes.byref(self.taskHandle)))
        self.CHK(nidaq.DAQmxCreateDOChan(self.taskHandle,
                                   addr,
                                   "",
                                   DAQmx_Val_ChanForAllLines
                                   ))
        self.CHK(nidaq.DAQmxStartTask(self.taskHandle))

    def __enter__(self, *args, **kwargs):
        """for context manager"""
        return self

    def __exit__(self, type, value, traceback):
        """for context manager"""
        self.cleanup()
        return value

    def CHK(self, err):
        """a simple error checking routine"""
        if err < 0:
            buf_size = 1000
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('nidaq call failed with error %d: %s' % (err,
                                        repr(buf.value)))
        if err > 0:
            buf_size = 1000
            buf = ctypes.create_string_buffer('\000' * buf_size)
            nidaq.DAQmxGetErrorString(err, ctypes.byref(buf), buf_size)
            raise RuntimeError('nidaq generated warning %d: %s' % (err,
                                            repr(buf.value)))

    def set_on(self, off=False):
        data = numpy.array(8*[not off]).astype(numpy.uint32)
        written = numpy.zeros_like(data)
        self.CHK(nidaq.DAQmxWriteDigitalU32(self.taskHandle,
                        1,  # numSampsPerCHan
                        int32(1),  # autoStart
                        float64(10.0),  # timeout
                        DAQmx_Val_GroupByChannel,  # dataLayout
                        data.ctypes.data,  # writeArray
                        written.ctypes.data,  # writeArray
                        None))

    def set_off(self):
        self.set_on(off=True)

    def cleanup(self):
        """Always cleanup, else DAQ hardware will lock"""
        self.set_off()
        nidaq.DAQmxStopTask(self.taskHandle)
        nidaq.DAQmxClearTask(self.taskHandle)

if __name__ == '__main__':
    import time

    # set ttl on
    ttl = daqmx_digital_out()
    print "TTL created"
    ttl.set_on()

    # listen to 3 channels
    nr_samples = 100
    channel1 = daqmx_channel_in(device=1, channel=0, num_samples=nr_samples)
    channel2 = daqmx_channel_in(device=1, channel=1, num_samples=nr_samples)
    channel3 = daqmx_channel_in(device=1, channel=2, num_samples=nr_samples)
    while True:
        print "Channel1 sum %.3f V" % channel1.read_voltage().sum() 
        print "Channel2 mean %.3f V" % channel2.read_voltage().mean()
        print "Channel3 std: %.3f V" % channel3.read_voltage().std()
        time.sleep(1)
#    # read channel1
#    import matplotlib
#    matplotlib.use('TkAgg')
#    import matplotlib.pyplot as plt
#    plt.ion()
#    fig = plt.figure()
#    nr_samples = 100
#    nr_rep = 10
#    channel1 = daqmx_channel_in(1, 0, num_samples=nr_samples)
#                                      ,clockspeed=48*1000)
#    #channel2 = daqmx_channel_in(1,num_samples=nr_samples)
#
#    points = []
#    allpoints = numpy.zeros((nr_rep, nr_samples))
#    #points2 = []
#    time_axis = []
#
#    ax = fig.add_subplot(111)
#    line, = ax.plot([], [])
#    line2, = ax.plot([], [])
#    ax.set_ylim(-10.1, 10.1)
#    ax.set_xlim(0, 5)
#
#    #time.sleep(5)
#    start = time.time()
#    for i in xrange(nr_rep):
#        data = channel1.read_voltage()
#        allpoints[i] = data
#        #data2 = channel2.read_voltage()
#        points.append(numpy.average(data))
#   #     points2.append(numpy.average(data2))
#        time_axis.append(i)
#        line.set_data(time_axis, points)
#        ax.set_xlim(0, i)
#        ax.set_ylim(min(points), max(points))
#    #    line2.set_data(time_axis, points2)
#        plt.draw()
#        #time.sleep(.01)
#
#    plt.show()

    #ax2 = fig.add_subplot(121)
#    plt.figure()
#    plt.plot(allpoints.reshape(1, nr_rep * nr_samples)[0])
#    plt.show()

    print (time.time() - start) / 100.0
    print "Acquired %d points" % channel1.read.value
    channel1.cleanup()
    channel2.cleanup()
    channel3.cleanup()

#channel1 = None

    ttl.cleanup()

#    raw_input()
