from logitech.g19 import G19
from logitech.applets.xplanet.xplanet import Xplanet

import time

if __name__ == '__main__':
    lg19 = G19(True)
    lg19.start_event_handling()
    try:
        xplanet = Xplanet(lg19)
        lg19.add_applet(xplanet)
        while True:
            time.sleep(10)
    finally:
        xplanet.stop()
        lg19.stop_event_handling()
