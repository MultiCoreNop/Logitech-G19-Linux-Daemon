from logitech.g19 import G19
from logitech.applets.simple_bg_light.simple_bg_light import SimpleBgLight
from logitech.applets.simple_display_brightness.simple_display_brightness \
        import SimpleDisplayBrightness
from logitech.applets.xplanet.xplanet import Xplanet

import time

if __name__ == '__main__':
    lg19 = G19(True)
    lg19.start_event_handling()
    try:
        bgLight = SimpleBgLight(lg19)
        lg19.add_applet(bgLight)

        xplanet = Xplanet(lg19)
        lg19.add_applet(xplanet)

        displayBrightness = SimpleDisplayBrightness(lg19)
        lg19.add_applet(displayBrightness)
        while True:
            time.sleep(10)
    finally:
        xplanet.stop()
        lg19.stop_event_handling()
