import usb

def find_device(idVendor, idProduct):
    for bus in usb.busses():
        for dev in bus.devices:
            if dev.idVendor == idVendor and \
                    dev.idProduct == idProduct:
                return dev
    return None

def open_lcd_control(dev):
    config = dev.configurations[0]
    iface = config.interfaces[1][0]
    ep = iface.endpoints[0]

    handle = dev.open()
    try:
        handle.detachKernelDriver(iface)
    except usb.USBError:
        pass
    handle.setConfiguration(config)
    handle.claimInterface(iface)
    return handle

def open_lcd_display(dev):
    config = dev.configurations[0]
    iface = config.interfaces[0][0]

    handle = dev.open()
    try:
        handle.detachKernelDriver(iface)
    except usb.USBError:
        pass
    handle.setConfiguration(config)
    handle.claimInterface(iface)
    return handle

def set_bg_color(dev, r, g, b):
    handle = open_lcd_control(dev)
    rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
    colorData = [7, r, g, b]
    handle.controlMsg(rtype, 0x09, colorData, 0x307, 0x01)

def set_display_brightness(dev, val):
    '''val in [0,100]'''
    data = [val, 0xe2, 0x12, 0x00, 0x8c, 0x11, 0x00, 0x10, 0x00]
    rtype = usb.TYPE_VENDOR | usb.RECIP_INTERFACE
    handle.controlMsg(rtype, 0x0a, data, 0x0, 0x0)

def set_display_color(dev, b1, b2):
    handle = open_lcd_display(dev)
    frame = [0x10, 0x0F, 0x00, 0x58, 0x02, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x3F, 0x01, 0xEF, 0x00, 0x0F]
    for i in range(16, 256):
        frame.append(i)
    for i in range(256):
        frame.append(i)
    for i in range(320 * 240):
        frame.append(b1)
        frame.append(b2)
    handle.bulkWrite(2, frame)

def main():
    pass

# if __name__ == '__main__':
#     main()

dev = find_device(0x046d, 0xc229)
if dev:
    #set_bg_color(dev, 255, 255, 0)
    #handle = open_lcd_control(dev)

    config = dev.configurations[0]
    iface = config.interfaces[1][0]

    handle = dev.open()
    handle.reset()
    try:
        handle.detachKernelDriver(iface)
    except usb.USBError as (e):
        print "usb error: ", str(e)
    handle.setConfiguration(config)
    handle.claimInterface(iface)

    rtype = usb.TYPE_CLASS | usb.RECIP_INTERFACE
