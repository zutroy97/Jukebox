import serial
import io
import time
from pubsub import pub
from threading import Thread
import logging

class JukeboxPanel(Thread):
    """Handles communication with the Jukebox Panel."""
    # ser = None
    # buff = ""
    # pub = None

    def __init__(self, pub=pub):
        super().__init__()
        self.ser = serial.Serial('/dev/cu.wchusbserial320', 9600)
        self.buff = ""
        logging.debug('Waiting for display to initalize.')
        self.wait()
        time.sleep(1) # Give arduino time to initialize
        self.clear()
        self.pub = pub
        pub.subscribe(self.trackChange, 'root.itunes.track.change')
    
    def wait(self):
        self.ser.readline()
        time.sleep(1)

    def _writeRaw(self, message):
        self.ser.write(message + b"\n")
        self.ser.readline()

    def write4(self, message):
        self.ser.write(b"w4 " + message + b"\n")
#        self.wait()

    def write3(self, message):
        self.ser.write(b"w3 " + message + b"\n")
#        self.wait()

    def clear(self):
        logging.debug("Clearing jukebox display")
        self._writeRaw(b"c")

    def trackChange(self, trackNumber):
        padding= '{0:0>3}'.format(trackNumber)
        logging.debug("Track Changed " + padding)
        self.write3(padding.encode('ascii'))

    def doRead(self):
        tic = time.time()
        while (self.ser.in_waiting > 0):
#            logging.debug('reading %s bytes', self.ser.in_waiting)
            self.buff += self.ser.read(self.ser.in_waiting).decode('ascii')
        lines = self.buff.split("\n")
        if (len(lines) == 0):
            return
        if (len(lines) == 1):
            self.buff = ""
            return lines[0].strip()
        self.buff = str.join("\n", lines[1:])
        return lines[0].strip()

    def run(self):
#        logging.debug('JukeboxPanel Thread Running')
        while(True):
            line = self.doRead()
            if (line.startswith('BTN:')):
#                logging.debug("BUTTON " + line[4])
                self.pub.sendMessage('root.jukebox.panel.button', button=line[4])
            elif (line == "READY>"):
#                logging.debug("Got READY> prompt")
                pass
            elif (line != ""):
                logging.debug("GOT MESSAGE " + line)
            time.sleep(.250)
