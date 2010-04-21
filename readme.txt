=== Logitech G19 Linux support ===

This is work in progress and considered absolutely alpha.  It SHOULD work, but no
guarantees are given.  If your keyboard goes up in flames, explodes and rapes
your hamster, don't say I didn't warn you!


=== What you need to use this ===

Python 2.6
pyusb (I'm using v0.4.2 atm)

optional:
xplanet
PySide (not yet)


=== What I want to do ===

Refactor and build an API+framework for applets.
Developers will get a simple way to create mini-programs of any kind.  An
infrastructure providing a base menu to select/activate applets and easy
possibilities to integrate into input handling will created.

So far it does not make much sense to start developing on the current code base
(as I just started to create this one week ago).  As soon as I stopped
experimenting, I'll change this file.


=== What it does right now ===

If invoked by "python main.py":

--- Color ---

By selecting M1..3 you select red/green/blue for manipulation.  Using the scroll
you can adjust the current backlight value.


--- Color ---

If no M-button is selected, scrolling will change the display brightness.


--- Xplanet ---

If you have 'xplanet' installed, you can press the "play"/"stop" buttons to
rotate the earth in your display.

(After pressing start, 360 images will be generated using as many CPUs as you
have, but nonetheless it will take up to three minutes.)

Currently I am working on supporting Qt on the display - let's see how far I
get...


=== How you can send anything you want to your G19 ===

Fire up a python shell.  The main API is logitech.g19.G19 atm:

>>> from logitech.g19 import G19

# if you get an error: lg19 = G19(True)
>>> lg19 = G19()

# setting backlight to red
>>> lg19.set_bg_color(255, 0, 0)

# fill your display with green
>>> lg19.fill_display_with_color(0, 255, 0)

# test your screen
>>> lg19.set_display_colorful()

# set backlight to blue after reset
# this will be your backlight color after a bus reset (or switching the keyboard
# off and no)
>>> lg19.save_default_bg_color(0, 0, 255)

# send an image to display
>>> data = [...] # format described in g19.py
>>> lg19.send_frame(data)

# load an arbitrary image from disk to display (will be resized non-uniform)
>>> lg19.load_image("/path/to/myimage.jpg")

# reset the keyboard via USB
>>> lg19.reset()
# now you have to rebuild the connection:
>>> lg19 = G19()


HINT: After creating a G19 object, your "light key" will not work anymore,
      because the keyboard waits for you to read its data.  You can start doing
      so by calling lg19.start_event_handling().
      (have a look at main.py)



As soon as I reach a stable point, I promise to write a lot of documentation. ;-)
