#pyserial pypubsub typing

import serial
import io
import time
from pubsub import pub
import threading
import logging
import JukeboxPanel


trackNumber = 1
logging.basicConfig(
    level=logging.DEBUG,
    format='(%(threadName)-10s) %(message)s',
)

def buttonPressed(button):
    global trackNumber
    logging.debug("Got button press " + button)
    if (button == 'R'):
        trackNumber = 1
        jb.clear()

pub.subscribe(buttonPressed, 'root.jukebox.panel.button')

jb = JukeboxPanel.JukeboxPanel(pub)
jb.start()


while (True):
#    print("Changing Track\n")
    pub.sendMessage('root.itunes.track.change', trackNumber=str(trackNumber))
    trackNumber += 1
    time.sleep(.5)


