TemperatureFeedback_ Reprate_
===========================


Use this program to perform feedback on the temperature controller of the baseplate of the laser with the error signal of the locked reprate. Will automagically determine wether the reprate is locking at that moment or not, and perform feedback only when the reprate is being locked.


=== Installation instructions on windows: ===
You'll need python and pygtk. Istallation instructions:


    1. Download python. You'll need the most recent version 2.x (for instance 2.7). [link](http://www.python.org/download/) or [direct link](http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi)
    2. Install python
    3. Download pygtk. Pygtk for windows can be downloaded [here](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/ ).( Direct link: [here](http://ftp.gnome.org/pub/GNOME/binaries/win32/pygtk/2.24/pygtk-all-in-one-2.24.2.win32-py2.7.msi) ). You'll need the most recent all-in-one installer available. 
    4. Install pygtk (this is also just a .exe)
    5. Add the python directory to your %PATH variable
        5a. Go to system properties -> advanced
        5b. Click enviroment variables
        5c. Select Path from the drop-down menu
        5d. Append ;C:\Python27\ to the path.
        5e. Click OK
    5. Restart your computer
    6. Download the "master" branch of the github website. 
    7. Unpack the file somewhere
    8. Go to the bin subdirectory, and make a shortcut to "powergui.bat" on the desktop. By clicking on it you can start the program.
    9. Download the zipped version of the program, unpack and you're ready to go.

=== Modifying the feedback parameters ===

The algorithm is as follows:

    * Check the standard deviation on the voltage of the PID. If it is high, the PID is on
    * If the PID is on:
        1. if the signal is within bounds: 
            2a. If the signal was within bounds for the last 20 s:
                2b. Mark that the signal was within bounds for the last 20s
            2a. continue
        2. if the signal is outside bounds:
            2a. if the signal was within bounds for the last N seconds: perform feedback
            2a. if not: continue


There are a few options to customize the feedback. They are listed below, with the file in which they can be changed

    * Lower and upper bound of the Temperature:  : self.lower_temperature_limit and self.upper_temperature_limit in T255Controller.py
    * Temperature step for the feedback: self.temperature_step in T255Controller.py _
    * Lower and upper bound of the error signal of the PID: self.min_signal, self.max_signal in temperatureFeedback.py (in class feedbackloop)
    * Number of points to keep: length_signals in feedbackloop
    * How long the signal should be within bounds before the temperature can be raised/lowered again: PID_within_bounds_time_ in temperaturefeedback.py
    * Discrimination values 
