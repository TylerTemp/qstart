# coding:utf-8
from __future__ import unicode_literals
import wx
import pyHook
import logging

import sys
import os
import imp

if (hasattr(sys, "frozen") # new py2exe
        or hasattr(sys, "importers") # old py2exe
        or imp.is_frozen("__main__")):
    ROOTDIR = os.path.dirname(sys.executable)
else:
    ROOTDIR = os.path.dirname(sys.argv[0])

try:
    __file__    # note py2exe can have __file__. refer into the `.exe` file
except NameError:
    LIBDIR = ROOTDIR
else:
    LIBDIR = os.path.normpath(os.path.join(__file__, '..', '..', '..'))

sys.path.insert(0, LIBDIR)
from lib.tool.translate import Translate
sys.path.pop(0)

logger = logging.getLogger('ui.catchkey')
_ = Translate().translate


class CatchKeyFrame(wx.Frame):
    key_id = -1
    KEY_ID = -1
    KEY_NAME = ''
    WIDGET = None
    # FORBID_OK_ONCE = False    # 空格会导致OK被按下. 如果是空格, 禁止OK一次
    FORCE_TRANCE = {
        "Oem_1": ";",
        "Oem_2": "/",
        "Oem_3": "~",
        "Oem_4": "[",
        "Oem_6": "]",
        "Oem_5": "\\",
        "Oem_7": "\"",
        "Oem_Comma": ",",
        "Oem_Period": ".",
        "Oem_Minus": "-",
        "Oem_Plus": "=",
    }

    def __init__(self, parent, hook_obj, id=-1, title=_('Catch a Hotkey')):
        super(CatchKeyFrame, self).__init__(
            parent, id, title,
            style=wx.FRAME_TOOL_WINDOW | wx.CAPTION| wx.FRAME_FLOAT_ON_PARENT
        )

        self.SetBackgroundColour('WHITE')
        self.parent = parent
        self.hook_obj = hook_obj
        self.sizer = self.create_sizer(self)
        self.key_hcs = pyHook.HookConstants()

    def create_sizer(self, parent):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text_box = wx.TextCtrl(parent, -1, '', style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOK, self.text_box)
        self.text_box.Enable(False)
        self.info = wx.StaticText(parent, -1, _('Please enter a key\n'),
                                  style=wx.ALIGN_CENTER| wx.ST_NO_AUTORESIZE)
        self.detail_title = wx.StaticText(parent, -1, _('ID:\nName:\nAlias:'))
        self.detail_context = wx.StaticText(parent, -1, '')
        self.button_OK = wx.Button(parent, -1, _('OK'))
        self.button_Reset = wx.Button(parent, -1, _('Reset'))
        button_Cancel = wx.Button(parent, -1, _('Cancel'))
        self.button_OK.Enable(False)

        self.Bind(wx.EVT_BUTTON, self.OnOK, self.button_OK)
        self.Bind(wx.EVT_BUTTON, self.OnReset, self.button_Reset)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, button_Cancel)



        main_sizer.Add(self.text_box, 0, wx.ALIGN_CENTER| wx.BOTTOM| wx.TOP, 5)
        main_sizer.Add(self.info, 0, wx.ALIGN_CENTER| wx.ALL, 5)

        sub_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sub_sizer.Add(self.detail_title, 1, wx.ALIGN_CENTER| wx.ALL, 5)
        sub_sizer.Add(self.detail_context, 1, wx.ALIGN_CENTER| wx.ALL, 5)
        main_sizer.Add(sub_sizer, 0, wx.ALIGN_CENTER| wx.ALL, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.Add(self.button_OK, 0, wx.ALIGN_RIGHT|wx.LEFT, 10)
        btn_sizer.Add(self.button_Reset, 0, wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT, 10)
        btn_sizer.Add(button_Cancel, 0, wx.ALIGN_RIGHT|wx.RIGHT, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER| wx.ALL, 5)

        parent.SetSizer(main_sizer)
        parent.Fit()
        return main_sizer

    def reset_frame(self, key_id, hook_handler, ok_handler, widget):
        logger.debug('set hook handler to %s', hook_handler)
        logger.debug('set ok handler to %s', ok_handler)

        self.KEY_ID = key_id
        self.hook_handler = hook_handler
        self.ok_handler = ok_handler
        self.WIDGET = widget

        self.Set_key(key_id)

    def Set_key(self, key_id, key_orl_name = ''):
        key_name = ''
        key_orl_name = self.key_hcs.IDToName(int(key_id))
        key_orl_name = self.FORCE_TRANCE.get(key_orl_name, key_orl_name)
        if key_orl_name is None:
            key_orl_name = _('Warning: this key may not be recognizable')
            self.text_box.SetValue('')
        else:
            self.text_box.SetValue(key_orl_name)

        if int(key_id) == -1:
                key_orl_name = ''
                key_id = ''
        elif key_id in self.parent.user_info:
            key_name = self.parent.user_info[key_id]['key']
            self.text_box.SetValue(key_name)

        detail_context = '\n'.join([key_id, key_orl_name, key_name])
        self.detail_context.SetLabel(detail_context)
        self.sizer.Layout()

    def key_manager(self, event):
        # if event.KeyID == 32:
        #     self.FORBID_OK_ONCE = True
        logger.debug('get event %s', event)
        self.key_id = str(event.KeyID)
        key_orl_name = event.Key
        self.release_key()
        self.Set_key(self.key_id, key_orl_name)
        return True

    def catch_key(self):
        # self.FORBID_OK_ONCE = False
        logger.debug('catching...')

        self.hook_obj.KeyDown = self.key_manager
        self.info.SetLabel(_("Please enter a key"))

        self.button_OK.Enable(False)
        self.button_Reset.Enable(False)
        self.text_box.Enable(False)
        logger.debug('catch finished')

        # self.Bind(wx.EVT_KEY_DOWN, self.Pass, self.button_OK)
        # self.Bind(wx.EVT_KEY_UP, self.Pass, self.button_OK)
        # self.Bind(wx.EVT_KEY_DOWN, self.Pass, self.button_Reset)
        # self.Bind(wx.EVT_KEY_UP, self.Pass, self.button_Reset)
        # self.button_OK.Bind(wx.EVT_KEY_DOWN, self.Pass)
        # self.button_OK.Bind(wx.EVT_KEY_UP, self.Pass)
        # self.button_Reset.Bind(wx.EVT_KEY_DOWN, self.Pass)
        # self.button_Reset.Bind(wx.EVT_KEY_UP, self.Pass)

    def release_key(self):
        logger.debug('released')
        self.hook_obj.KeyDown = self.hook_handler
        self.info.SetLabel(_('You can rename the button in the box above'))

        self.button_Reset.Enable(True)
        self.text_box.Enable(True)

        if int(self.key_id) == 32:
            wx.CallLater(100, self.button_OK.Enable)
            wx.CallLater(101, self.button_OK.SetFocus)
        else:
            self.button_OK.Enable(True)
            self.button_OK.SetFocus()

        # self.button_OK.Unbind(wx.EVT_KEY_DOWN)
        # self.button_OK.Unbind(wx.EVT_KEY_UP)
        # self.button_Reset.Unbind(wx.EVT_KEY_DOWN)
        # self.button_Reset.Unbind(wx.EVT_KEY_UP)
        return True

    def FocusKey(self):
        self.button_OK.SetFocus()

    def OnCancel(self, event):
        self.release_key()
        self.Show(False)

    def OnReset(self, event):
        logger.debug('catch key...')
        self.catch_key()

    def OnOK(self, event):
        # if self.FORBID_OK_ONCE:
        #     self.FORBID_OK_ONCE = False
        #     return
        self.KEY_ID = self.key_id
        self.KEY_NAME = self.text_box.GetValue()
        self.Show(False)
        self.ok_handler(self.KEY_ID, self.KEY_NAME, self.WIDGET)

    def Pass(self, event):
        return

    def __del__(self):
        self.Destory()

if __name__ == '__main__':
    import pythoncom, pyHook
    import json
    from QStart import MyFrame
    from collections import OrderedDict

    app = wx.PySimpleApp()
    hm = pyHook.HookManager()

    with file('key_clean_info.json', 'r') as f:
        key_info = json.load(f)
    user_info = OrderedDict(
            {
            '81':{'key':'Q','flag':False, 'name': 'IEx64', 'cmd':r'C:\Program Files\Internet Explorer\iexplore.exe'},            #Q-IEx64
            '87':{'key':'W','flag':False, 'name': 'IEx86', 'cmd':r'C:\Program Files (x86)\Internet Explorer\iexplore.exe'},      #W-IEx86
            '70':{'key':'F','flag':False, 'name': 'Firefox', 'cmd':r'E:\MozillaFirefox\firefox.exe'},                              #F-FireFox
            '71':{'key':'G','flag':False, 'name': 'Chrome', 'cmd':r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'},#G-GoogleChrome
            '69':{'key':'D','flag':True , 'name': 'Douban', 'cmd':r'C:/Users/Tyler/AppData/Local/Douban/Radio/DoubanRadio.exe'},  #D-DoubanFM
            '72':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '73':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '74':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '75':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '76':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '77':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '78':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '79':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '80':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '82':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            '83':{'key':'D','flag':True , 'name': '测试', 'cmd': '测试'},
            }
        )
    parent = MyFrame(key_info=key_info, user_info=user_info)
    dlg = CatchKeyFrame(parent, hm, parent.KeyManager, -1)
    dlg.catch_key()
    dlg.ShowModal()

    print(dlg.GetReturnCode())
    dlg.Destroy()

    hm.HookKeyboard()
    pythoncom.PumpMessages()
    app.MainLoop()
