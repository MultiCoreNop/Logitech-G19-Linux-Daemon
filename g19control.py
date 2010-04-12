import time
import usb

# data received from keyboard for M-keys
# received packet is [0x02, 0x00, key, 0x40]
# these are also the bit fields for setting the currently illuminated keys
# (see set_enabled_m_keys())
KEY_M1 = 0x80
KEY_M2 = 0x40
KEY_M3 = 0x20
KEY_MR = 0x10

# special keys at display
# The current state of pressed keys is an OR-combination of the following
# codes.
# Incoming data always has 0x80 appended, e.g. pressing and releasing the menu
# key results in two INTERRUPT transmissions: [0x04, 0x80] and [0x00, 0x80]
# Pressing (and holding) UP and OK at the same time results in [0x88, 0x80].
KEY_BACK = 0x02
KEY_DOWN = 0x40
KEY_LEFT = 0x20
KEY_MENU = 0x04
KEY_OK = 0x08
KEY_RIGHT = 0x10
KEY_SETTINGS = 0x01
KEY_UP = 0x80

# specific codes sent by G-keys
# received as [0x02, keyH, keyL, 0x40]
# example: G3: [0x02, 0x04, 0x00, 0x40]
#          G1 + G2 + G11: [0x03, 0x04, 0x00, 0x40]
KEY_G01 = 0x0001
KEY_G02 = 0x0002
KEY_G03 = 0x0004
KEY_G04 = 0x0008
KEY_G05 = 0x0010
KEY_G06 = 0x0020
KEY_G07 = 0x0040
KEY_G08 = 0x0080
KEY_G09 = 0x0100
KEY_G10 = 0x0200
KEY_G11 = 0x0400
KEY_G12 = 0x0800

# light switch
# this on is similar to G-keys:
# down: [0x02, 0x00, 0x00, 0x48]
# up:   [0x02, 0x00, 0x00, 0x40]
KEY_LIGHT = 0x08

# winkey switch to winkey off: [0x03, 0x01]
# winkey switch to winkey on:  [0x03, 0x00]
KEY_WIN_SWITCH = 0x0103

# multimedia keys
# received as [0x01, key]
# example: NEXT+SCROLL_UP:       [0x01, 0x21]
#          after scroll stopped: [0x01, 0x01]
#          after release:        [0x01, 0x00]
KEY_NEXT = 0x01
KEY_PREV = 0x02
KEY_STOP = 0x05
KEY_PLAY = 0x08
KEY_MUTE = 0x10
SCROLL_UP = 0x20
SCROLL_DOWN = 0x40


class LogitechG19(object):
    '''Simple access to Logitech G19 features.

    The G19 consists of two composite USB devices:
        * 046d:c228
          The keyboard consisting of two interfaces:
              MI00: keyboard
                  EP 0x81(in)  - INT the keyboard itself
              MI01:
                  EP 0x82(in)  - multimedia keys, incl. scroll and Winkey-switch

        * 046d:c229
          LCD display with two interfaces:
              MI00 (0x05):
                  EP 0x81(in)  - INT display keys
                  EP 0x02(out) - BULK display itself
              MI01 (0x06): backlight
                  EP 0x83(in)  - INT G-keys, M1..3/MR key, light key

    '''

    def __init__(self):
        self.__device = self._find_device(0x046d, 0xc229)
        if not self.__device:
            raise usb.USBError("G19 not found on USB bus")
        self.__handle = self.__open_handle(self.__device)
        self.__use_lcd_control()
        self.__use_lcd_display()

    @staticmethod
    def _find_device(idVendor, idProduct):
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == idVendor and \
                        dev.idProduct == idProduct:
                    return dev
        return None

    @staticmethod
    def __open_handle(dev):
        handle = dev.open()
        return handle

    @staticmethod
    def rgb_to_uint16(r, g, b):
        '''Converts a RGB value to 16bit highcolor (5-6-5).

        @return 16bit highcolor value in little-endian.

        '''
        rBits = r * 2**5 / 255
        gBits = g * 2**6 / 255
        bBits = b * 2**5 / 255

        rBits = rBits if rBits <= 0b00011111 else 0b00011111
        gBits = gBits if gBits <= 0b00111111 else 0b00111111
        bBits = bBits if bBits <= 0b00011111 else 0b00011111

        valueH = (rBits << 3) | (gBits >> 3)
        valueL = (gBits << 5) | bBits
        return valueL << 8 | valueH

    def __use_lcd_control(self):
        try:
            self.__handle.releaseInterface()
        except (ValueError, usb.USBError):
            pass
        config = self.__device.configurations[0]
        iface = config.interfaces[1][0]
        try:
            self.__handle.detachKernelDriver(iface)
        except usb.USBError:
            pass
        self.__handle.setConfiguration(config)
        self.__handle.claimInterface(iface)

    def __use_lcd_display(self):
        try:
            self.__handle.releaseInterface()
        except (ValueError, usb.USBError):
            pass
        config = self.__device.configurations[0]
        iface = config.interfaces[0][0]
        try:
            self.__handle.detachKernelDriver(iface)
        except usb.USBError:
            pass
        self.__handle.setConfiguration(config)
        self.__handle.claimInterface(iface)

    def reset(self):
        self.__use_lcd_display()
        self.__handle.reset()
        self.__use_lcd_control()
        self.__handle.reset()
        self = LogitechG19()

    def send_frame(self, data):
        '''Sends a frame to display.

        @param data 320x240x2 bytes, containing the frame in little-endian
        16bit highcolor (5-6-5) format.
        Image must be row-wise, starting at upper left corner and ending at
        lower right.  This means (data[0], data[1]) is the first pixel and
        (data[239 * 2], data[239 * 2 + 1]) the lower left one.

        '''
        if len(data) != (320 * 240 * 2):
            raise ValueError("illegal frame size: " + str(len(data))
                    + " should be 320x240x2=" + str(320 * 240 * 2))
        self.__use_lcd_display()
        frame = [0x10, 0x0F, 0x00, 0x58, 0x02, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x3F, 0x01, 0xEF, 0x00, 0x0F]
        for i in range(16, 256):
            frame.append(i)
        for i in range(256):
            frame.append(i)

        for i in range(320 * 240 * 2):
            frame.append(data[i])
        self.__handle.bulkWrite(2, frame, 1000)

    def set_bg_color(self, r, g, b):
        self.__use_lcd_control()
        rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
        colorData = [7, r, g, b]
        self.__handle.controlMsg(rtype, 0x09, colorData, 0x307, 0x01, 1000)

    def set_enabled_m_keys(self, keys):
        '''Sets currently lit keys as an OR-combination of KEY_M1..3, KEY_MR.

        '''
        self.__use_lcd_control()
        rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
        self.__handle.controlMsg(rtype, 0x09, [5, keys], 0x305, 0x01, 1000)

    def set_display_brightness(self, val):
        '''val in [0,100]'''
        self.__use_lcd_control()
        data = [val, 0xe2, 0x12, 0x00, 0x8c, 0x11, 0x00, 0x10, 0x00]
        rtype = usb.TYPE_VENDOR | usb.RECIP_INTERFACE
        self.__handle.controlMsg(rtype, 0x0a, data, 0x0, 0x0)

    def set_display_color(self, r, g, b):
        # 16bit highcolor format: 5 red, 6 gree, 5 blue
        # saved in little-endian, because USB is little-endian
        value = self.rgb_to_uint16(r, g, b)
        valueH = value & 0xff
        valueL = value >> 8
        frame = [valueL, valueH] * (320 * 240)
        self.send_frame(frame)

    def set_display_colorful(self):
        '''This is an example how to create an image having a green to red
        transition from left to right and a black to blue from top to bottom.

        '''
        data = []
        for i in range(320 * 240 * 2):
            data.append(0)
        for x in range(320):
            for y in range(240):
                data[2*(x*240+y)] = lg19.rgb_to_uint16(
                    255 * x / 320, 255 * (320 - x) / 320, 255 * y / 240) >> 8
                data[2*(x*240+y)+1] = lg19.rgb_to_uint16(
                    255 * x / 320, 255 * (320 - x) / 320, 255 * y / 240) & 0xff
        self.send_frame(data)


def main():
    pass

# if __name__ == '__main__':
#     main()
lg19 = LogitechG19()
