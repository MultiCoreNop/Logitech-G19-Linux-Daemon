import threading
import time

class Runnable(object):
    '''Helper object to create thread content objects doing periodic tasks.

    Override execute() in inherited class.  This will be called until the
    thread is stopped.  A Runnable can be started multiple times opposed to
    threading.Thread.

    '''

    def __init__(self):
        self.__keepRunning = True
        self.__mutex = threading.Lock()

    def execute(self):
        '''This method must be implemented and will be executed in an infinite
        loop as long as stop() was not called.

        An implementation is free to check is_about_to_stop() at any time to
        allow a clean termination of current processing before reaching the end
        of execute().
        
        '''
        pass

    def is_about_to_stop(self):
        '''Returns whether this thread will terminate after completing the
        current execution cycle.

        @return True if thread will terminate after current execution cycle.

        '''
        self.__mutex.acquire()
        val = self.__keepRunning
        self.__mutex.release()
        return not val

    def run(self):
        '''Implements the infinite loop.  Do not override, but override
        execute() instead.

        '''
        while not self.is_about_to_stop():
            self.execute()

    def start(self):
        '''Starts the thread.  If stop() was called, but start() was not, run()
        will do nothing.

        '''
        self.__mutex.acquire()
        self.__keepRunning = True
        self.__mutex.release()

    def stop(self):
        '''Flags this thread to be terminated after next completed execution
        cycle.  Calling this method will NOT stop the thread instantaniously,
        but will complete the current operation and terminate in a clean way.

        '''
        self.__mutex.acquire()
        self.__keepRunning = False
        self.__mutex.release()


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
            time.sleep(0.02)
