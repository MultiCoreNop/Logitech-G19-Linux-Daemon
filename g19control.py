import time
import usb

class LogitechG19(object):
    '''Simple access to Logitech G19 features.

    The G19 consists of two composite USB devices:
        * 046d:c228
          The keyboard consisting of two interfaces:
              MI00 - the keyboard itself (2 endpoints)
              MI01 - multimedia keys, incl. scroll and Winkey-switch
                     (1 endpoint)
        * 046d:c229
          LCD display with two interfaces:
              MI00 - the display itself (2 endpoints)
              MI01 - M1..3/MR keys, G-keys, backlight, light-key (1 endpoint)

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
        rBits = (r * 2**5 / 255) & 0b00011111
        gBits = (g * 2**6 / 255) & 0b00111111
        bBits = (b * 2**5 / 255) & 0b00011111
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
        self.__handle.reset()

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
        # on avg. only every 2nd call succeeds - dunno why
        while True:
            try:
                self.__handle.bulkWrite(2, frame, 100)
                break
            except usb.USBError:
                time.sleep(0.01)

    def set_bg_color(self, r, g, b):
        self.__use_lcd_control()
        rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
        colorData = [7, r, g, b]
        self.__handle.controlMsg(rtype, 0x09, colorData, 0x307, 0x01)

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
