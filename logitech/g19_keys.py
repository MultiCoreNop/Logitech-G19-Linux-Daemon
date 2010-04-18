class Key(object):
    '''Static container containing all keys.'''

    # G/M keys
    # light switch
    LIGHT, \
    M1, \
    M2, \
    M3, \
    MR, \
    G01, \
    G02, \
    G03, \
    G04, \
    G05, \
    G06, \
    G07, \
    G08, \
    G09, \
    G10, \
    G11, \
    G12 = range(17)

    # special keys at display
    BACK, \
    DOWN, \
    LEFT, \
    MENU, \
    OK, \
    RIGHT, \
    SETTINGS, \
    UP = range(G12 + 1, G12 + 9)

    # multimedia keys
    WINKEY_SWITCH, \
    NEXT, \
    PREV, \
    STOP, \
    PLAY, \
    MUTE, \
    SCROLL_UP, \
    SCROLL_DOWN = range(UP + 1, UP + 9)

    mmKeys = set([
            WINKEY_SWITCH,
            NEXT,
            PREV,
            STOP,
            PLAY,
            MUTE,
            SCROLL_UP,
            SCROLL_DOWN])


class Data(object):
    '''Static container with all data values for all keys.'''

    # special keys at display
    # The current state of pressed keys is an OR-combination of the following
    # codes.
    # Incoming data always has 0x80 appended, e.g. pressing and releasing the menu
    # key results in two INTERRUPT transmissions: [0x04, 0x80] and [0x00, 0x80]
    # Pressing (and holding) UP and OK at the same time results in [0x88, 0x80].
    displayKeys = {}
    displayKeys[0x01] = Key.SETTINGS
    displayKeys[0x02] = Key.BACK
    displayKeys[0x04] = Key.MENU
    displayKeys[0x08] = Key.OK
    displayKeys[0x10] = Key.RIGHT
    displayKeys[0x20] = Key.LEFT
    displayKeys[0x40] = Key.DOWN
    displayKeys[0x80] = Key.UP

    # these are the bit fields for setting the currently illuminated keys
    # (see set_enabled_m_keys())
    LIGHT_KEY_M1 = 0x80
    LIGHT_KEY_M2 = 0x40
    LIGHT_KEY_M3 = 0x20
    LIGHT_KEY_MR = 0x10

    # specific codes sent by M- and G-keys
    # received as [0x02, keyL, keyH, 0x40]
    # example: G3: [0x02, 0x04, 0x00, 0x40]
    #          G1 + G2 + G11: [0x02, 0x03, 0x04, 0x40]
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
    KEY_M1 = 0x1000
    KEY_M2 = 0x2000
    KEY_M3 = 0x4000
    KEY_MR = 0x8000

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
    mmKeys = {}
    mmKeys[0x01] = Key.NEXT
    mmKeys[0x02] = Key.PREV
    mmKeys[0x04] = Key.STOP
    mmKeys[0x08] = Key.PLAY
    mmKeys[0x10] = Key.MUTE
    mmKeys[0x20] = Key.SCROLL_UP
    mmKeys[0x40] = Key.SCROLL_DOWN
