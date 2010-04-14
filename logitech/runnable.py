import threading

class Runnable(object):
    '''Helper object to create thread content objects doing periodic tasks, or
    tasks supporting premature termination.

    Override execute() in inherited class.  This will be called until the
    thread is stopped.  A Runnable can be started multiple times opposed to
    threading.Thread.

    To write a non-periodic task that should support premature termination,
    simply override run() and call is_about_to_stop() at possible termination
    points.

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
