from logitech.g19_keys import Key
from logitech.g19_receivers import InputProcessor

class SimpleBgLight(object):

    def __init__(self):
        pass

    def get_input_processor(self):
        return self

    def process_input(self, evt):
        pass
