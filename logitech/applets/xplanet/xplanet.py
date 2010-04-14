import multiprocessing
import os
import tempfile
import time
import threading
from logitech.g19 import *
from logitech.g19_receivers import *


class EarthImageCreator(threading.Thread):
    '''Thread for calling xplanet for specific angles.'''

    def __init__(self, angleStart, angleStop, slot, dataStore):
        '''Creates images for angles [angleStart, angleStop] (including) and
        stores a the list of frames via dataStore.store(slot, frames).

        After completion of each frame, dataStore.signal_frame_done() will be
        called.

        '''
        threading.Thread.__init__(self)
        self.__slot = slot
        self.__dataStore = dataStore
        self.__angleStart = angleStart
        self.__angleStop = angleStop

    def run(self):
        frames = []
        try:
            handle, filename = tempfile.mkstemp('.bmp')
            os.close(handle)
            
            for i in range(self.__angleStart, self.__angleStop + 1):
                cmdline = "xplanet -geometry 320x240 -output "
                cmdline += filename
                cmdline += " -num_times 1 -longitude "
                cmdline += str(i)
                os.system(cmdline)
                frames.append( lg19.convert_image_to_frame(filename) );
                dataStore.signal_frame_done()
        finally:
            os.remove(filename)
        self.__dataStore.store(self.__slot, frames)


class DataStore(object):
    '''Maintains all xplanet generated frames.'''

    def __init__(self):
        self.__numThreads = multiprocessing.cpu_count()
        self.__data = [[]] * self.__numThreads
        self.__lock = threading.Lock()
        self.__framesDone = 0

    def get_data(self):
        '''Returns all currently available data.

        @return List of all frames.  If no frames are calculated, an empty list
        will be returned.

        '''
        self.__lock.acquire()
        allFrames = []
        for frame in self.__data:
            allFrames += frame
        self.__lock.release()
        return allFrames

    def signal_frame_done(self):
        self.__lock.acquire()
        self.__framesDone += 1
        print "frames done: {0}".format(self.__framesDone)
        self.__lock.release()

    def update(self):
        '''Regenerates all data.'''
        self.__lock.acquire()
        self.__framesDone = 0
        self.__data = [[]] * self.__numThreads
        self.__lock.release()
        creators = []

        for i in range(self.__numThreads):
            perCpu = 360 / self.__numThreads
            angleStart = i * perCpu
            if i == self.__numThreads - 1:
                angleStop = 359
            else:
                angleStop = angleStart + perCpu - 1
            c = EarthImageCreator(angleStart, angleStop, i, self)
            creators.append(c)
            c.start()

        for creator in creators:
            creator.join()

    def store(self, slot, frames):
        self.__lock.acquire()
        print "committing {0}".format(slot)
        self.__data[slot] = frames
        self.__lock.release()


if __name__ == '__main__':
    lg19 = G19()

    frames = []
    print "...loading frames..."

    dataStore = DataStore()
    dataStore.update()
    frames = dataStore.get_data()
    print "done"

    fps = 25
    lastTime = time.clock()

    while True:
        for frame in frames:
            now = time.clock()
            diff = lastTime - now + (1.0 / fps)
            if diff > 0:
                time.sleep(diff)
            lastTime = time.clock()
            lg19.send_frame(frame)
