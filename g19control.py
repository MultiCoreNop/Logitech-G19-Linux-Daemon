import time
import usb

class LogitechG19(object):

    def __init__(self):
        self.__device = self._find_device(0x046d, 0xc229)
        if not self.__device:
            raise usb.USBError("G19 not found on USB bus")
        self.__handle = self.__open_handle(self.__device)

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
        self.__use_lcd_display()
        frame = [0x10, 0x0F, 0x00, 0x58, 0x02, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x3F, 0x01, 0xEF, 0x00, 0x0F]
        for i in range(16, 256):
            frame.append(i)
        for i in range(256):
            frame.append(i)

        # 16bit highcolor format: 5 red, 6 gree, 5 blue
        # saved in little-endian, because USB is little-endian
        rBits = (r * 2^5 / 255) & 0b00011111
        gBits = (g * 2^6 / 255) & 0b00111111
        bBits = (b * 2^5 / 255) & 0b00011111
        valueH = (rBits << 3) | (gBits >> 3)
        valueL = (gBits << 5) | bBits

        for i in range(320 * 240):
            frame.append(valueL)
            frame.append(valueH)
        # on avg. only every 2nd call succeeds - dunno why
        while True:
            try:
                self.__handle.bulkWrite(2, frame, 100)
                break
            except usb.USBError:
                time.sleep(0.01)

def main():
    pass

# if __name__ == '__main__':
#     main()
lg19 = LogitechG19()
