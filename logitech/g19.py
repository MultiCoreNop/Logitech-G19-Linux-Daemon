from g19_receivers import G19Receiver

import sys
import threading
import time
import usb
import PIL.Image as Img

class G19(object):
    '''Simple access to Logitech G19 features.

    All methods are thread-safe if not denoted otherwise.

    '''

    def __init__(self, resetOnStart=False):
        '''Initializes and opens the USB device.'''
        self.__usbDevice = G19UsbController(resetOnStart)
        self.__usbDeviceMutex = threading.Lock()
        self.__keyReceiver = G19Receiver(self)
        self.__threadDisplay = None

    @staticmethod
    def convert_image_to_frame(filename):
        '''Loads image from given file.

        Format will be auto-detected.  If neccessary, the image will be resized
        to 320x240.

        @return Frame data to be used with send_frame().

        '''
        img = Img.open(filename)
        access = img.load()
        if img.size != (320, 240):
            img = img.resize((320, 240), Img.CUBIC)
            access = img.load()
        data = []
        for x in range(320):
            for y in range(240):
                r, g, b = access[x, y]
                val = G19.rgb_to_uint16(r, g, b)
                data.append(val >> 8)
                data.append(val & 0xff)
        return data

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

    def add_applet(self, applet):
        '''Starts an applet.'''
        self.__keyReceiver.add_input_processor(applet.get_input_processor())

    def fill_display_with_color(self, r, g, b):
        '''Fills display with given color.'''
        # 16bit highcolor format: 5 red, 6 gree, 5 blue
        # saved in little-endian, because USB is little-endian
        value = self.rgb_to_uint16(r, g, b)
        valueH = value & 0xff
        valueL = value >> 8
        frame = [valueL, valueH] * (320 * 240)
        self.send_frame(frame)

    def load_image(self, filename):
        '''Loads image from given file.

        Format will be auto-detected.  If neccessary, the image will be resized
        to 320x240.

        '''
        self.send_frame(self.convert_image_to_frame(filename))

    def read_g_and_m_keys(self, maxLen=20):
        '''Reads interrupt data from G, M and light switch keys.

        @return maxLen Maximum number of bytes to read.
        @return Read data or empty list.

        '''
        self.__usbDeviceMutex.acquire()
        val = []
        try:
            val = list(self.__usbDevice.handleIf1.interruptRead(
                0x83, maxLen, 10))
        except usb.USBError:
            pass
        finally:
            self.__usbDeviceMutex.release()
        return val

    def read_display_menu_keys(self):
        '''Reads interrupt data from display keys.

        @return Read data or empty list.

        '''
        self.__usbDeviceMutex.acquire()
        val = []
        try:
            val = list(self.__usbDevice.handleIf0.interruptRead(0x81, 2, 10))
        except usb.USBError:
            pass
        finally:
            self.__usbDeviceMutex.release()
        return val

    def read_multimedia_keys(self):
        '''Reads interrupt data from multimedia keys.

        @return Read data or empty list.

        '''
        self.__usbDeviceMutex.acquire()
        val = []
        try:
            val = list(self.__usbDevice.handleIfMM.interruptRead(0x82, 2, 10))
        except usb.USBError:
            pass
        finally:
            self.__usbDeviceMutex.release()
        return val

    def reset(self):
        '''Initiates a bus reset to USB device.'''
        self.__usbDeviceMutex.acquire()
        try:
            self.__usbDevice.reset()
        finally:
            self.__usbDeviceMutex.release()

    def save_default_bg_color(self, r, g, b):
        '''This stores given color permanently to keyboard.

        After a reset this will be color used by default.

        '''
        rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
        colorData = [7, r, g, b]
        self.__usbDeviceMutex.acquire()
        try:
            self.__usbDevice.handleIf1.controlMsg(
                rtype, 0x09, colorData, 0x308, 0x01, 1000)
        finally:
            self.__usbDeviceMutex.release()

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
        frame = [0x10, 0x0F, 0x00, 0x58, 0x02, 0x00, 0x00, 0x00,
                 0x00, 0x00, 0x00, 0x3F, 0x01, 0xEF, 0x00, 0x0F]
        for i in range(16, 256):
            frame.append(i)
        for i in range(256):
            frame.append(i)

        frame += data

        self.__usbDeviceMutex.acquire()
        try:
            self.__usbDevice.handleIf0.bulkWrite(2, frame, 1000)
        finally:
            self.__usbDeviceMutex.release()

    def set_bg_color(self, r, g, b):
        '''Sets backlight to given color.'''
        rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
        colorData = [7, r, g, b]
        self.__usbDeviceMutex.acquire()
        try:
            self.__usbDevice.handleIf1.controlMsg(
                rtype, 0x09, colorData, 0x307, 0x01, 10)
        finally:
            self.__usbDeviceMutex.release()

    def set_enabled_m_keys(self, keys):
        '''Sets currently lit keys as an OR-combination of LIGHT_KEY_M1..3,R.

        example:
            from logitech.g19_keys import Data
            lg19 = G19()
            lg19.set_enabled_m_keys(Data.LIGHT_KEY_M1 | Data.LIGHT_KEY_MR)

        '''
        rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
        self.__usbDeviceMutex.acquire()
        try:
            self.__usbDevice.handleIf1.controlMsg(
                rtype, 0x09, [5, keys], 0x305, 0x01, 10)
        finally:
            self.__usbDeviceMutex.release()

    def set_display_brightness(self, val):
        '''Sets display brightness.

        @param val in [0,100] (off..maximum).

        '''
        data = [val, 0xe2, 0x12, 0x00, 0x8c, 0x11, 0x00, 0x10, 0x00]
        rtype = usb.TYPE_VENDOR | usb.RECIP_INTERFACE
        self.__usbDeviceMutex.acquire()
        try:
            self.__usbDevice.handleIf1.controlMsg(rtype, 0x0a, data, 0x0, 0x0)
        finally:
            self.__usbDeviceMutex.release()

    def set_display_colorful(self):
        '''This is an example how to create an image having a green to red
        transition from left to right and a black to blue from top to bottom.

        '''
        data = []
        for i in range(320 * 240 * 2):
            data.append(0)
        for x in range(320):
            for y in range(240):
                data[2*(x*240+y)] = self.rgb_to_uint16(
                    255 * x / 320, 255 * (320 - x) / 320, 255 * y / 240) >> 8
                data[2*(x*240+y)+1] = self.rgb_to_uint16(
                    255 * x / 320, 255 * (320 - x) / 320, 255 * y / 240) & 0xff
        self.send_frame(data)

    def start_event_handling(self):
        '''Start event processing (aka keyboard driver).

        This method is NOT thread-safe.

        '''
        self.stop_event_handling()
        self.__threadDisplay = threading.Thread(
                target=self.__keyReceiver.run)
        self.__keyReceiver.start()
        self.__threadDisplay.start()

    def stop_event_handling(self):
        '''Stops event processing (aka keyboard driver).

        This method is NOT thread-safe.

        '''
        self.__keyReceiver.stop()
        if self.__threadDisplay:
            self.__threadDisplay.join()
            self.__threadDisplay = None


class G19UsbController(object):
    '''Controller for accessing the G19 USB device.

    The G19 consists of two composite USB devices:
        * 046d:c228
          The keyboard consisting of two interfaces:
              MI00: keyboard
                  EP 0x81(in)  - INT the keyboard itself
              MI01: (ifacMM)
                  EP 0x82(in)  - multimedia keys, incl. scroll and Winkey-switch

        * 046d:c229
          LCD display with two interfaces:
              MI00 (0x05): (iface0) via control data in: display keys
                  EP 0x81(in)  - INT
                  EP 0x02(out) - BULK display itself
              MI01 (0x06): (iface1) backlight
                  EP 0x83(in)  - INT G-keys, M1..3/MR key, light key

    '''

    def __init__(self, resetOnStart=False):
        self.__lcd_device = self._find_device(0x046d, 0xc229)
        if not self.__lcd_device:
            raise usb.USBError("G19 LCD not found on USB bus")
        self.__kbd_device = self._find_device(0x046d, 0xc228)
        if not self.__kbd_device:
            raise usb.USBError("G19 keyboard not found on USB bus")
        self.handleIf0 = self.__lcd_device.open()
        if resetOnStart:
            self.handleIf0.reset()
            self.handleIf0 = self.__lcd_device.open()

        self.handleIf1 = self.__lcd_device.open()
        self.handleIfMM = self.__kbd_device.open()
        config = self.__lcd_device.configurations[0]
        iface0 = config.interfaces[0][0]
        iface1 = config.interfaces[1][0]

        try:
            self.handleIfMM.setConfiguration(1)
        except usb.USBError:
            pass

        try:
            self.handleIf1.detachKernelDriver(iface1)
        except usb.USBError:
            pass

        try:
            self.handleIfMM.detachKernelDriver(1)
        except usb.USBError:
            pass

        self.handleIf0.setConfiguration(1)
        self.handleIf1.setConfiguration(1)
        self.handleIf0.claimInterface(iface0)
        self.handleIf1.claimInterface(iface1)
        self.handleIfMM.claimInterface(1)

    @staticmethod
    def _find_device(idVendor, idProduct):
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == idVendor and \
                        dev.idProduct == idProduct:
                    return dev
        return None

    def reset(self):
        '''Resets the device on the USB.'''
        self.handleIf0.reset()
        self.handleIf1.reset()

def main():
    lg19 = G19()
    lg19.start_event_handling()
    time.sleep(20)
    lg19.stop_event_handling()

if __name__ == '__main__':
    main()
