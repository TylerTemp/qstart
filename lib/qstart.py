from __future__ import unicode_literals

import logging
import pythoncom
import wx
import locale
import json
import sys
import os
import imp

if (hasattr(sys, "frozen") or  # new py2exe
        hasattr(sys, "importers") or  # old py2exe
        imp.is_frozen("__main__")):
    ROOTDIR = os.path.dirname(sys.executable)
else:
    ROOTDIR = os.path.dirname(sys.argv[0])

try:
    __file__  # note py2exe can have __file__. refer into the `.exe` file
except NameError:
    LIBDIR = ROOTDIR
else:
    LIBDIR = os.path.normpath(os.path.join(__file__, '..'))

sys.path.insert(0, LIBDIR)
from lib.ui.mainframe import MainFrame
from lib.tool.translate import Translate
from lib.tool.minsix import open
sys.path.pop(0)

logger = logging.getLogger('main')


def main(lang=None, on_icon=None):
    cfg_file = os.path.join(ROOTDIR, MainFrame.USER_INFO)
    if os.path.exists(cfg_file):
        with open(cfg_file, 'r', encoding='utf-8') as f:
            s = f.read()
            if not s:
                logger.debug('user config empty')
                obj = {}
            else:
                obj = json.loads(s)
    else:
        logger.debug('user config file not found')
        obj = {}

    if lang is None:
        lang = obj.get('lang', locale.getdefaultlocale()[0])

    translator = Translate()

    logger.debug('try use language %s', lang)
    translator.lang = lang
    if translator.lang is None:
        if lang == 'en_US':
            logger.info('language set to default(en_US)')
        else:
            logger.info('language %s not support. Use default', lang)
    else:
        logger.info('language set to: %s', translator.lang)

    if on_icon is None:
        on_icon = obj.get('start_on_icon', False)
        MainFrame.start_on_icon = on_icon
        MainFrame.IS_SHOW = not on_icon

    logger.info('start on icon: %s', on_icon)

    app = wx.App(False)
    frame = MainFrame()
    frame.Show(not on_icon)
    pythoncom.PumpMessages()
    return app.MainLoop()

if __name__ == '__main__':
    logger.debug('starting...')
    main()
    logger.info('started')
