from runnable import Runnable

import threading
import time

class G19Receiver(Runnable):
    '''This receiver consumes all data sent by special keys.'''

    def __init__(self, g19):
        Runnable.__init__(self)
        self.__g19 = g19

    def execute(self):
        gotData = False
        data = self.__g19.read_multimedia_keys()
        if data:
            print "mm:  ", data
            gotData = True
        data = self.__g19.read_g_and_m_keys()
        if data:
            print "m/g: ", data
            gotData = True
        data = self.__g19.read_display_menu_keys()
        if data:
            print "dis: ", data
            gotData = True
        if not gotData:
            time.sleep(0.03)
