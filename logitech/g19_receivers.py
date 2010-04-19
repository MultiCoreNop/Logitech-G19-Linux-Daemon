from g19_keys import (Data, Key)
from runnable import Runnable

import threading
import time

class InputProcessor(object):
    '''Object to process key presses.'''

    def process_input(self, inputEvent):
        '''Processes given event.

        Should return as fast as possible.  Any time-consuming processing
        should be done in another thread.

        @param inputEvent Event to process.
        @return True if event was consumed, or False if ignored.

        '''
        return False


class InputEvent(object):
    '''Event created by a key press or release.'''

    def __init__(self, oldState, newState, keysDown, keysUp):
        '''Creates an InputEvent.

        @param oldState State before event happened.
        @param newState State after event happened.
        @param keysDown Keys newly pressed.
        @param keysUp Kys released by this event.

        '''
        self.oldState = oldState
        self.newState = newState
        self.keysDown = keysDown
        self.keysUp = keysUp


class State(object):
    '''Current state of keyboard.'''

    def __init__(self):
        self.__keysDown = set()

    def _data_to_keys_g_and_m(self, data):
        '''Converts a G/M keys data package to a set of keys defined as
        pressed by it.

        '''
        if len(data) != 4 or data[0] != 2:
            raise ValueError("not a multimedia key packet: " + str(data))
        empty = 0x400000
        curVal = data[3] << 16 | data[2] << 8 | data[1]
        keys = []
        while curVal != empty:
            foundAKey = False
            for val in Data.gmKeys.keys():
                if val & curVal == val:
                    curVal ^= val
                    keys.append(Data.gmKeys[val])
                    foundAKey = True
            if not foundAKey:
                raise ValueError("incorrect g/m key packet: " +
                        str(data))

        return set(keys)

    def _data_to_keys_mm(self, data):
        '''Converts a multimedia keys data package to a set of keys defined as
        pressed by it.

        '''
        if len(data) != 2 or data[0] not in [1, 3]:
            raise ValueError("not a multimedia key packet: " + str(data))
        if data[0] == 1:
            curVal = data[1]
            keys = []
            while curVal:
                foundAKey = False
                for val in Data.mmKeys.keys():
                    if val & curVal == val:
                        curVal ^= val
                        keys.append(Data.mmKeys[val])
                        foundAKey = True
                if not foundAKey:
                    raise ValueError("incorrect multimedia key packet: " +
                            str(data))
        elif data == [3, 1]:
            keys = [Key.WINKEY_SWITCH]
        elif data == [3, 0]:
            keys = []
        else:
            raise ValueError("incorrect multimedia key packet: " + str(data))

        return set(keys)

    def _update_keys_down(self, possibleKeys, keys):
        '''Updates internal keysDown set.

        Updates the current state of all keys in 'possibleKeys' with state
        given in 'keys'.

        Example:
        Currently set as pressed in self.__keysDown: [A, B]
        possibleKeys: [B, C, D]
        keys: [C]

        This would set self.__keysDown to [A, C] and return ([C], [B])

        @param possibleKeys Keys whose state could be given as 'pressed' at the
        same time by 'keys'.
        @param keys Current state of all keys in possibleKeys.
        @return A pair of sets listing newly pressed and newly released keys.

        '''
        keysDown = set()
        keysUp = set()
        for key in possibleKeys:
            if key in keys:
                if key not in self.__keysDown:
                    self.__keysDown.add(key)
                    keysDown.add(key)
            else:
                if key in self.__keysDown:
                    self.__keysDown.remove(key)
                    keysUp.add(key)
        return (keysDown, keysUp)

    def clone(self):
        '''Returns an exact copy of this state.'''
        state = State()
        state.__keysDown = set(self.__keysDown)
        return state

    def packet_received_g_and_m(self, data):
        '''Mutates the state by given data packet from G- and M- keys.

        @param data Data packet received.
        @return InputEvent for data packet, or None if data packet was ignored.

        '''
        oldState = self.clone()
        evt = None
        if len(data) == 4:
            keys = self._data_to_keys_g_and_m(data)
            keysDown, keysUp = self._update_keys_down(Key.gmKeys, keys)
            newState = self.clone()
            evt = InputEvent(oldState, newState, keysDown, keysUp)
        return evt

    def packet_received_mm(self, data):
        '''Mutates the state by given data packet from multimedia keys.

        @param data Data packet received.
        @return InputEvent for data packet.

        '''
        oldState = self.clone()
        if len(data) != 2:
            raise ValueError("incorrect multimedia key packet: " + str(data))
        keys = self._data_to_keys_mm(data)
        winKeySet = set([Key.WINKEY_SWITCH])
        if data[0] == 1:
            # update state of all mm keys
            possibleKeys = Key.mmKeys.difference(winKeySet)
            keysDown, keysUp = self._update_keys_down(possibleKeys, keys)
        else:
            # update winkey state
            keysDown, keysUp = self._update_keys_down(winKeySet, keys)
        newState = self.clone()
        return InputEvent(oldState, newState, keysDown, keysUp)


class G19Receiver(Runnable):
    '''This receiver consumes all data sent by special keys.'''

    def __init__(self, g19):
        Runnable.__init__(self)
        self.__g19 = g19
        self.__ips = []
        self.__mutex = threading.Lock()
        self.__state = State()

    def add_input_processor(self, processor):
        '''Adds an input processor.'''
        self.__mutex.acquire()
        self.__ips.append(processor)
        self.__mutex.release()
        pass

    def execute(self):
        gotData = False
        processors = self.list_all_input_processors()

        data = self.__g19.read_multimedia_keys()
        if data:
            evt = self.__state.packet_received_mm(data)
            if evt:
                for proc in processors:
                    if proc.process_input(evt):
                        break
            else:
                print "mm ignored: ", data
            gotData = True

        data = self.__g19.read_g_and_m_keys()
        if data:
            evt = self.__state.packet_received_g_and_m(data)
            if evt:
                for proc in processors:
                    if proc.process_input(evt):
                        break
            else:
                print "m/g ignored: ", data
            gotData = True

        data = self.__g19.read_display_menu_keys()
        if data:
            print "dis: ", data
            gotData = True

        if not gotData:
            time.sleep(0.03)

    def list_all_input_processors(self):
        '''Returns a list of all input processors currently registered to this
        receiver.

        @return All registered processors.  This list is a copy of the internal
        one.

        '''
        self.__mutex.acquire()
        allProcessors = list(self.__ips)
        self.__mutex.release()
        return allProcessors
