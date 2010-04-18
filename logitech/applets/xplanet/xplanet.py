from logitech.g19 import *
from logitech.g19_keys import Key
from logitech.g19_receivers import *
from logitech.runnable import Runnable

import multiprocessing
import os
import tempfile
import threading
import time


class EarthImageCreator(Runnable):
    '''Thread for calling xplanet for specific angles.'''

    def __init__(self, lg19, angleStart, angleStop, slot, dataStore):
        '''Creates images for angles [angleStart, angleStop) and stores a the
        list of frames via dataStore.store(slot, frames).

        After completion of each frame, dataStore.signal_frame_done() will be
        called.

        '''
        Runnable.__init__(self)
        self.__angleStart = angleStart
        self.__angleStop = angleStop
        self.__dataStore = dataStore
        self.__lg19 = lg19
        self.__slot = slot

    def run(self):
        frames = []
        try:
            handle, filename = tempfile.mkstemp('.bmp')
            os.close(handle)
            
            for i in range(self.__angleStart, self.__angleStop):
                if self.is_about_to_stop():
                    break
                cmdline = "xplanet -geometry 320x240 -output "
                cmdline += filename
                cmdline += " -num_times 1 -latitude 40 -longitude "
                cmdline += str(i)
                os.system(cmdline)
                frames.append( self.__lg19.convert_image_to_frame(filename) );
                self.__dataStore.signal_frame_done()
        finally:
            os.remove(filename)
        self.__dataStore.store(self.__slot, frames)


class DataStore(object):
    '''Maintains all xplanet generated frames.'''

    def __init__(self, lg19):
        self.__allFrames = []
        self.__creators = []
        self.__numThreads = multiprocessing.cpu_count()
        self.__lg19 = lg19
        self.__data = [[]] * self.__numThreads
        self.__lock = threading.Lock()
        self.__framesDone = 0

    def abort_update(self):
        self.__lock.acquire()
        for creator in self.__creators:
            creator.stop()
        self.__lock.release()

    def get_data(self):
        '''Returns all currently available data.

        @return List of all frames.  If no frames are calculated, an empty list
        will be returned.

        '''
        self.__lock.acquire()
        frames = self.__allFrames
        self.__lock.release()
        return frames

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
        threads = []

        for i in range(self.__numThreads):
            perCpu = 360 / self.__numThreads
            angleStart = i * perCpu
            if i == self.__numThreads - 1:
                angleStop = 360
            else:
                angleStop = angleStart + perCpu
            c = EarthImageCreator(self.__lg19, angleStart, angleStop, i, self)
            self.__lock.acquire()
            self.__creators.append(c)
            self.__lock.release()
            c.start()
            t = threading.Thread(target=c.run)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.__lock.acquire()
        self.__creators = []
        self.__allFrames = []
        for frame in self.__data:
            self.__allFrames += frame
        self.__lock.release()

    def store(self, slot, frames):
        self.__lock.acquire()
        print "committing {0}".format(slot)
        self.__data[slot] = frames
        self.__lock.release()


class XplanetRenderer(Runnable):
    '''Renderer which renderes current data from DataStore.'''

    def __init__(self, lg19, dataStore):
        Runnable.__init__(self)
        self.__dataStore = dataStore
        self.__fps = 25
        self.__lastTime = time.clock()
        self.__lg19 = lg19

    def execute(self):
        frames = reversed(self.__dataStore.get_data())
        if not frames:
            time.sleep(1)
        counter = 0
        for frame in frames:
            counter += 1
            if counter > self.__fps:
                counter = 0
                if self.is_about_to_stop():
                    break
            now = time.clock()
            diff = self.__lastTime - now + (1.0 / self.__fps)
            if diff > 0:
                time.sleep(diff)
            self.__lastTime = time.clock()
            self.__lg19.send_frame(frame)


class XplanetInputProcessor(InputProcessor):

    def __init__(self, xplanet):
        self.__xplanet = xplanet

    def process_input(self, inputEvent):
        processed = False
        if Key.PLAY in inputEvent.keysDown:
            self.__xplanet.start()
            processed = True
        if Key.STOP in inputEvent.keysDown:
            self.__xplanet.stop()
            processed = True
        return processed


class Xplanet(object):

    def __init__(self, lg19):
        self.__dataStore = DataStore(lg19)
        self.__lg19 = lg19
        self.__renderer = XplanetRenderer(lg19, self.__dataStore)
        self.__inputProcessor = XplanetInputProcessor(self)

    def get_input_processor(self):
        return self.__inputProcessor

    def start(self):
        t = threading.Thread(target=self.__dataStore.update)
        t.start()
        t = threading.Thread(target=self.__renderer.run)
        self.__renderer.start()
        t.start()

    def stop(self):
        self.__renderer.stop()
        self.__dataStore.abort_update()


if __name__ == '__main__':
    lg19 = G19()
    xplanet = Xplanet(lg19)
    xplanet.start()
    try:
        while True:
            time.sleep(10)
    finally:
        xplanet.stop()
