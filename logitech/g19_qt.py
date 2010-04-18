from PyQt4 import QtCore
from PyQt4 import QtGui


def convert_image(img):
    data = [0] * (320 * 240 * 2)
    for x in range(320):
        for y in range(240):
            val = img.pixel(x, y)
            data[2*(x * 240 + y)] = val >> 8
            data[2*(x * 240 + y) + 1] = val & 0xff
    return data


QtGui.QApplication.setGraphicsSystem("raster");
app = QtGui.QApplication(["-graphicssystem", "raster"])
img = QtGui.QImage(320, 240, QtGui.QImage.Format_RGB16)

class Fuck(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setAttribute(QtCore.Qt.WA_PaintOnScreen)

    def paintEngine(self):
        return img.paintEngine()

    #def paintEvent(self, evt):
    #    evt.accept()
    #    self.render(img)

def logit(func):
    def wrapped(*lols):
        print "called"
        return fund(*lols)
    return wrapped

#QtGui.QWidget.paintEngine = lambda a: img.paintEngine()
w = QtGui.QWidget()

#w = Fuck()
w.resize(320,240)
l = QtGui.QVBoxLayout(w)
w.setLayout(l)

text1 = QtGui.QLabel("text1", w)
l.addWidget(text1)

text2 = QtGui.QLabel("text2", w)
l.addWidget(text2)

button1 = QtGui.QPushButton("Push me now", w)
l.addWidget(button1)

button2 = QtGui.QPushButton("Cancel this shit", w)
l.addWidget(button2)

w.render(img)
data = convert_image(img)

from logitech.g19 import G19
lg19 = G19()
lg19.reset()

lg19 = G19()
lg19.send_frame(data)

evtDownPress = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Down, QtCore.Qt.NoModifier)
evtDownRelease = QtGui.QKeyEvent(QtCore.QEvent.KeyRelease, QtCore.Qt.Key_Down, QtCore.Qt.NoModifier)

QtCore.QCoreApplication.postEvent(w, evtDownPress)
QtCore.QCoreApplication.postEvent(w, evtDownRelease)

w.render(img)
data = convert_image(img)

evtDownPress = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Tab, QtCore.Qt.NoModifier)
evtDownRelease = QtGui.QKeyEvent(QtCore.QEvent.KeyRelease, QtCore.Qt.Key_Tab, QtCore.Qt.NoModifier)

QtCore.QCoreApplication.postEvent(w, evtDownPress)
QtCore.QCoreApplication.postEvent(w, evtDownRelease)


# Xvfb :1 -screen 0 320x240x16 -fbdir /tmp/lala 
# xwud -in /tmp/lala/Xvfb_screen0
# xwdtopnm
