from logitech.g19_keys import (Data, Key)
from logitech.g19_receivers import InputProcessor

class SimpleDisplayBrightness(object):
    '''Simple adjustment of display brightness.

    Uses scroll to adjust display brightness.

    '''

    def __init__(self, lg19):
        self.__lg19 = lg19
        self.__curBrightness = 100

    @staticmethod
    def _clamp_brightness(val):
        '''Clamps given value to [0, 100].'''
        val = val if val >= 0 else 0
        val = val if val <= 100 else 100
        return val

    def get_input_processor(self):
        return self

    def process_input(self, evt):
        usedInput = False
        diffVal = 0

        if Key.SCROLL_UP in evt.keysDown:
            diffVal = 5
            usedInput = True
        if Key.SCROLL_DOWN in evt.keysDown:
            diffVal = -5
            usedInput = True

        oldVal = self.__curBrightness
        newVal = self._clamp_brightness(oldVal + diffVal)

        if oldVal != newVal:
            self.__lg19.set_display_brightness(newVal)
            self.__curBrightness = newVal
        return usedInput
