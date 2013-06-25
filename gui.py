import gtk
import numpy as np
import time
import gobject
import matplotlib
matplotlib.use('gtkAgg')
from matplotlib.figure import Figure
from temperatureFeedback import feedbackLoop
from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
import sys

class FeedbackApp:

    def __init__(self):
        # initialize the feedbackloop
        gtk.threads_init()
        gtk.threads_enter()
        self.feedbackloop = feedbackLoop()
        self.feedbackloop.active = False
        self.feedbackloop.start()
        gtk.threads_leave()

        # create a window
        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win.set_size_request(600,500)
        self.win.connect('destroy', gtk.main_quit)

        #vbox to put everything in
        self.vbox = gtk.VBox()
        self.win.add(self.vbox)

        # add a graph
        self.figure = Figure(figsize=(10,4))
        self.figureCanvas = FigureCanvas(self.figure)
        self.vbox.pack_start(self.figureCanvas, expand=True, fill=True)

        # graph
        self.axes = self.figure.add_subplot(111)
        self.axes.grid()

        self.line, = self.axes.plot([1,2,3,4,5],[5,3,5,2,5],'-^', label='output signal PID')

        # topline
        self.topline, = self.axes.plot([-1e99, 1e99], 2*[self.feedbackloop.max_signal], label='upper lim')
        self.botline, = self.axes.plot([-1e99, 1e99], 2*[self.feedbackloop.min_signal], label='lower lim')
        self.figureCanvas.draw()
        self.axes.legend(loc=2)


        # button start/stop
        self.buttonBox = gtk.HButtonBox()
        self.vbox.pack_end(self.buttonBox, expand=False, fill=True)

        self.startStopButton = gtk.ToggleButton('Start/Stop')
        self.startStopButton.connect('toggled', self.activateFeedbackLoop)
        self.buttonBox.pack_start(self.startStopButton)


        self.win.show_all()
        gobject.idle_add(self.update_graph)

    def activateFeedbackLoop(self, *args):
        """ Activate the feedbackloop """
        if self.startStopButton.get_active():
            print "ctivating feedback"
        self.feedbackloop.active = self.startStopButton.get_active()

        



    # add a start/stop box


    def update_graph(self):
        """ Update the graphical representation of the feedback loop"""
        xdata = self.feedbackloop.time_history.toArray()
        order = np.argsort(xdata)
        xdata = xdata[order]
        ydata = self.feedbackloop.signal_history.toArray()
        ydata = ydata[order]

        self.line.set_xdata(xdata)
        self.line.set_ydata(ydata)
        self.figureCanvas.draw()
        try:
            if not (None in xdata.tolist()):
                self.axes.set_xlim(min(xdata),max(xdata))
            else:
                self.axes.set_xlim(max(xdata)-20, max(xdata))
            self.axes.set_ylim(0,5)
        except:
            pass

        return True

        


if __name__ == '__main__':
    FeedbackApp()

    # start

    gtk.main()
