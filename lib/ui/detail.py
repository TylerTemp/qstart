# coding:utf-8
from __future__ import unicode_literals
import wx
import json
import logging

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
    __file__    # note py2exe can have __file__. refer into the `.exe` file
except NameError:
    LIBDIR = rootdir
else:
    LIBDIR = os.path.normpath(os.path.join(__file__, '..', '..', '..'))

sys.path.insert(0, LIBDIR)
from lib.tool.minsix import open
from lib.tool.translate import Translate
sys.path.pop(0)

logger = logging.getLogger('ui.detail')
_ = Translate().translate

abs_file = os.path.join(ROOTDIR, 'src', 'config', 'basic_cmd.json')
with open(abs_file, 'r+', encoding='utf-8') as f:
    BASIC_CMD = json.load(f)

HOT_KEY_BUTTON_ID = wx.NewId()


class DetailFrame(wx.Frame):
    KEY_ID = '0'
    KEY_NAME = ''
    CMD = ''
    CMD_NAME = ''
    LINE_SIZER = None
    FLAG = True
    DISABLE_COLOR = 'LIGHT GREY'
    BACKUP_CMD = ''
    BACKUP_FILE = ''

    def __init__(self, parent, id=-1, title=_('Set Information')):
        super(DetailFrame, self).__init__(
            parent, id, title,
            style=wx.FRAME_TOOL_WINDOW | wx.CAPTION | wx.FRAME_FLOAT_ON_PARENT
        )

        self.SetBackgroundColour('WHITE')
        sizer = self.create_sizer()
        self.SetSizer(sizer)
        self.Fit()
        x, y = self.GetSize()
        self.SetSize((350, y))

    def create_sizer(self):

        lable_hot_key = wx.StaticText(self, -1, _('Hotkey:'))
        self.button_hot_key = wx.Button(self, HOT_KEY_BUTTON_ID, '')
        label_cmd_name = wx.StaticText(self, -1, _('Name:'))
        self.combo_cmd_name = wx.ComboBox(
            self,
            -1,
            choices=list(map(_, BASIC_CMD.keys())),
            style=wx.CB_DROPDOWN)

        self.radio_file = wx.RadioButton(self, -1, _('Open/Run a File'),
                                         style=wx.RB_GROUP)
        self.text_file = wx.TextCtrl(self, -1)
        self.button_select_file = wx.Button(self, -1, '...',
                                            style=wx.BU_EXACTFIT)
        self.radio_cmd = wx.RadioButton(self, -1, _('Run a Command'))
        self.text_cmd = wx.TextCtrl(self, -1)

        self.button_ok = wx.Button(self, -1, _('OK'))
        self.button_cancel = wx.Button(self, -1, _('Cancel'))

        self.button_hot_key.key_id = '0'

        self.Bind(wx.EVT_BUTTON, self.OnSetHotkey, self.button_hot_key)
        self.Bind(wx.EVT_COMBOBOX, self.OnComboChoice, self.combo_cmd_name)
        self.Bind(wx.EVT_BUTTON, self.OnSelectFile, self.button_select_file)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnActiveFile, self.radio_file)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnActiveCmd, self.radio_cmd)
        self.Bind(wx.EVT_TEXT, self.OnActiveFile, self.text_file)
        self.Bind(wx.EVT_TEXT, self.OnActiveCmd, self.text_cmd)
        self.text_file.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.text_cmd.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)

        self.Bind(wx.EVT_BUTTON, self.OnOkButton, self.button_ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancelButton, self.button_cancel)

        radio_no_use = wx.RadioButton(self, -1, '', style=wx.RB_GROUP)
        size = radio_no_use.GetSize()
        radio_no_use.Show(False)
        radio_no_use.Destroy()
        del radio_no_use

        sizer = wx.BoxSizer(wx.VERTICAL)

        info_sizer = wx.BoxSizer(wx.HORIZONTAL)
        info_sizer.Add(lable_hot_key, 0, wx.ALL, 5)
        info_sizer.Add(self.button_hot_key, 0, wx.ALL, 5)
        info_sizer.Add(label_cmd_name, 0, wx.ALL, 5)
        info_sizer.Add(self.combo_cmd_name, 0, wx.ALL, 5)
        sizer.Add(info_sizer, 0, wx.ALL | wx.EXPAND, 10)

        sizer.Add(self.radio_file, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 15)

        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        file_sizer.Add(size, 0, wx.LEFT | wx.RIGHT, 5)
        file_sizer.Add(self.text_file, 1, wx.LEFT | wx.RIGHT, 5)
        file_sizer.Add(self.button_select_file, 0, wx.LEFT | wx.RIGHT, 5)
        sizer.Add(file_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        sizer.Add(self.radio_cmd, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 15)

        cmd_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cmd_sizer.Add(size, 0, wx.ALL, 5)
        cmd_sizer.Add(self.text_cmd, 1, wx.ALL, 5)
        cmd_sizer.Add(self.button_select_file.GetSize(), 0, wx.ALL, 5)
        sizer.Add(cmd_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        ok_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_sizer.Add(wx.Size(-1, -1), 1, wx.EXPAND | wx.ALL, 5)
        ok_sizer.Add(self.button_ok, 0, wx.EXPAND | wx.ALL, 5)
        ok_sizer.Add(self.button_cancel, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(ok_sizer, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        return sizer

    def reset_frame(self, key_id, key_name, cmd, cmd_name, flag,
                    line_sizer, ok_handler):
        self.KEY_ID = key_id
        self.KEY_NAME = key_name
        self.CMD = cmd
        self.CMD_NAME = cmd_name
        self.FLAG = flag
        self.LINE_SIZER = line_sizer
        self.ok_handler = ok_handler

        self.button_hot_key.SetLabel(key_name)
        self.button_hot_key.key_id = key_id

        self.combo_cmd_name.SetValue(cmd_name)
        colors = [self.DISABLE_COLOR, 'WHITE']
        self.text_cmd.SetBackgroundColour(colors.pop(flag))
        self.text_file.SetBackgroundColour(colors[0])

        if flag:
            self.BACKUP_CMD = cmd
            self.BACKUP_FILE = ''
            self.text_cmd.SetValue(cmd)
            self.text_file.SetValue('')
        else:
            self.BACKUP_FILE = cmd
            self.BACKUP_CMD = ''
            self.text_cmd.SetValue('')
            self.text_file.SetValue(cmd)

        self.radio_cmd.SetValue(flag)
        self.radio_file.SetValue(not flag)

    def change_key(self, key_id, key_name, widget):
        self.SetFocus()
        self.button_hot_key.key_id = key_id
        self.button_hot_key.SetLabel(key_name)

    def OnSetHotkey(self, event):
        parent = self.GetParent()
        parent.catch_key_frame.Show(False)
        parent.catch_key_frame.reset_frame(
            self.button_hot_key.key_id, parent.key_manager, self.change_key,
            self.button_hot_key)
        parent.catch_key_frame.Set_key(
            self.button_hot_key.key_id, self.button_hot_key.GetLabel())
        parent.catch_key_frame.catch_key()
        parent.catch_key_frame.Show(True)
        parent.catch_key_frame.SetFocus()

    def OnSelectFile(self, event):
        abs_file = wx.FileSelector(_('Select a file you want to open'))
        if abs_file:
            self.SetFocusFile()
            self.text_file.SetValue(abs_file)

    def OnComboChoice(self, event):
        self.SetFocusCmd()
        self.text_cmd.SetValue(
            BASIC_CMD[self.combo_cmd_name.GetStringSelection()])

    def OnSetFocus(self, event):
        obj = event.GetEventObject()
        event.Skip()
        if obj is self.text_file:
            self.SetFocusFile()
        elif obj is self.text_cmd:
            self.SetFocusCmd()

    def SetFocusFile(self):
        self.radio_file.SetValue(True)
        self.text_file.SetBackgroundColour('WHITE')
        self.text_cmd.SetBackgroundColour(self.DISABLE_COLOR)
        self.text_file.SetValue(self.BACKUP_FILE)
        self.text_cmd.Clear()
        self.text_file.Refresh()
        self.text_cmd.Refresh()
        return

    def SetFocusCmd(self):

        self.radio_cmd.SetValue(True)
        self.text_file.SetBackgroundColour(self.DISABLE_COLOR)
        self.text_cmd.SetBackgroundColour('WHITE')
        self.text_file.Clear()
        self.text_cmd.SetValue(self.BACKUP_CMD)
        self.text_file.Refresh()
        self.text_cmd.Refresh()
        return

    def OnActiveFile(self, event):
        obj = event.GetEventObject()
        if obj is self.radio_cmd:
            self.SetFocusCmd()
            return
        if obj is self.radio_file:
            self.SetFocusFile()
            return
        text = obj.GetValue()
        if text:
            if obj is self.text_file:
                self.BACKUP_FILE = text
            elif obj is self.text_cmd:
                self.BACKUP_CMD = text
        event.Skip()

    def OnActiveCmd(self, event):
        self.OnActiveFile(event)

    def OnOkButton(self, event):
        self.KEY_ID = self.button_hot_key.key_id
        self.KEY_NAME = self.button_hot_key.GetLabel()
        self.CMD_NAME = self.combo_cmd_name.GetValue()
        self.FLAG = self.radio_cmd.GetValue()
        if self.FLAG:
            elem = self.text_cmd
        else:
            elem = self.text_file
        self.CMD = elem.GetValue()
        self.Show(False)
        self.GetParent().catch_key_frame.Show(False)
        self.ok_handler(self.KEY_ID, self.KEY_NAME, self.CMD, self.CMD_NAME,
                        self.FLAG, self.LINE_SIZER)

    def OnCancelButton(self, event):
        self.Show(False)


if __name__ == '__main__':
    app = wx.PySimpleApp()
    DetailFrame(wx.Frame(None)).Show()
    app.MainLoop()
