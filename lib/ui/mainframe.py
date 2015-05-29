# coding: utf-8
from __future__ import unicode_literals
import pythoncom
import pyHook
import subprocess
import json
import ctypes
import logging
import wx
import locale
try:
    from wx.adv import HyperlinkCtrl
except ImportError:
    from wx import HyperlinkCtrl

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
from lib.tool.minsix import open
from lib.tool.translate import Translate
from lib.ui.detail import DetailFrame
from lib.ui.catchkey import CatchKeyFrame
from lib.ui.taskbaricon import TaskBarIcon
from lib.ui.about import AboutBox
sys.path.pop(0)

logger = logging.getLogger('ui.mainframe')
translator = Translate()
_ = translator.translate
phoenix = ('phoenix' in wx.version())

if not phoenix:
    wx.FD_SAVE = wx.SAVE
    wx.FD_OVERWRITE_PROMPT = wx.OVERWRITE_PROMPT

class MainFrame(wx.Frame):

    # Main window is shown? (To solve taskbar icon double click problem)
    IS_SHOW = True
    # Is it catching the key?
    IS_RUN  = True

    start_on_icon = False

    ID_OPEN = wx.NewId()
    ID_SAVE = wx.NewId()
    ID_SAVEAS = wx.NewId()
    ID_QUIT = wx.NewId()
    ID_TASKBAR = wx.NewId()
    ID_RUN = wx.NewId()  # check tool
    ID_STOP = wx.NewId()  # check tool

    ID_LASTLINE_KEY = wx.NewId()  # last line setting button
    ID_LASTLINE_DETAIL = wx.NewId()  # last line "..." button

    USER_INFO = 'src/config/user_info.json'
    KEY_INFO  = 'src/config/key_info.json'
    ABOUT_INFO= 'about.json'
    ICON = 'src/img/main.ico'
    ICO_TITLE = 'src/img/About.png'
    ICO = ICO_TITLE
    VERSION = '1.1.0'

    STATUSBAR_WIDTH_2 = [-1, 75]
    # STATUSBAR_WIDTH_3_1 = [-5, -2, -1]
    STATUSBAR_WIDTH_3 = [-1, -1, 75]

    KEY_LIST = []
    def __init__(
        self, key_obj=None, key_info=None, user_info=None,
        parent=None, id=-1, title=_('QStart'),
        pos=wx.DefaultPosition, size=(450, 350),
        style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
                ):

        super(self.__class__, self).__init__(parent, id, title, pos, size, style)

        self.INIT_LANG = translator.lang
        self.current_lang = translator.lang

        self.SetBackgroundColour('WHITE')

        self.key_obj = pyHook.HookManager()
        self.key_obj.HookKeyboard()
        self.key_obj.KeyUp = self.key_up
        self.key_obj.KeyDown = self.key_manager
        self.key_hcs = pyHook.HookConstants()
        self.key_1, self.key_2, self.user_info = \
            self.user_data(os.path.join(ROOTDIR, self.USER_INFO))

        self.key_info = self.key_data()
        self.toolbar = self.create_tool_bar()
        self.statusbar = self.create_status_bar()

        self.menubar = self.create_menu_bar()
        for each in self.to_check_id:
            self.menubar.FindItem(each)[0].Check(True)
        del self.to_check_id
        self.sizer = self.create_main_sizer()

        self.reset_scroll_window()

        self.catch_key_frame = CatchKeyFrame(self, self.key_obj)
        self.detail_frame = DetailFrame(self)
        self.SetIcon(wx.Icon(os.path.join(ROOTDIR, self.ICON), wx.BITMAP_TYPE_ICO))
        self.taskbar_icon = TaskBarIcon(self)
        self.about_dlg = self.create_about_dlg()

        self.SetRun(True)
        self.DragAcceptFiles(True)
        self.Bind(wx.EVT_DROP_FILES, self.OnOpen)
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnEnterTool)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)

    @property
    def menu_data(self):
        self.to_check_id = []

        sys_lang = locale.getdefaultlocale()[0]
        support = translator.support(sys_lang)
        if support:
            text = _('System(%s)') % sys_lang
            lang_text = _('Use the system default language(%s)') % sys_lang
        else:
            text = _('System(%s)(not support)') % sys_lang
            lang_text = (_('Use the system default language(%s)(not support)') %
                         sys_lang)

        default_lang_id = wx.NewId()
        en_lang_id = wx.NewId()

        if self.current_lang is None:
            self.to_check_id.append(default_lang_id)
        elif self.current_lang == 'en_US':
            self.to_check_id.append(en_lang_id)

        language_items = [(default_lang_id, text, lang_text,
                           lambda evt: self.OnChangeLang(evt, None),
                           wx.ITEM_RADIO),
                          (en_lang_id,
                           _('English(en_US)'),
                           _('Set language to English(en_US)'),
                           lambda evt: self.OnChangeLang(evt, 'en_US'),
                           wx.ITEM_RADIO)]
        for each in translator.supported():
            _id = wx.NewId()
            if self.current_lang == each['code']:
                self.to_check_id.append(_id)
            language_items.append(
                (_id,
                 '%s(%s)' % (each['name'], each['eng_name']),
                 _('Set language to %s(%s)(restart program needed)') %
                    (each['name'], each['eng_name']),
                 lambda evt: self.OnChangeLang(evt, each['code']),
                 wx.ITEM_RADIO))

        return {
             _('&File'): (
                (self.ID_OPEN, _('&Open a config') + '\tCtrl+O',
                 _('Load a config file'), self.OnOpen),
                # (self.ID_SAVE, u'储存配置(&Save)...\tCtrl+S', u'储存配置', self.OnSave),
                (self.ID_SAVEAS, _('S&ave as') + '\tCtrl+Shift+S',
                 _('Export the config'), self.OnSaveAs),
                (wx.ID_SEPARATOR, '', '', None),
                (self.ID_QUIT, _('&Quit') + '\tAlt+F4',
                 _('Fully exit program'), self.OnQuit),
            ),
            _('&Config'): (
                {_('&Language'): language_items},
                (wx.ID_SEPARATOR, '', '', None),
                {_('&Startup on'):
                    ((wx.NewId(), _('&Window'),
                     _('Show window when startup'),
                     lambda evt: self.OnIconStartup(evt, False),
                     wx.ITEM_RADIO),
                     (wx.NewId(), _('Taskbar &Icon'),
                      _('Hide in taskbar icon when startup'),
                      lambda evt: self.OnIconStartup(evt, True),
                      wx.ITEM_RADIO))},
                (wx.ID_SEPARATOR, '', '', None),
                (self.ID_RUN, _('&Run'), _('Run QStart'), self.OnRun, wx.ITEM_RADIO),
                (self.ID_STOP, _('&Pause'), _('Pause QStart'), self.OnStop, wx.ITEM_RADIO),
                (wx.ID_SEPARATOR, '', '', None),
                (self.ID_TASKBAR, _('&iconify') + '\tCtrl+H', _('Minimize to a taskbar icon'), self.OnHide),
             ),
             _('&About'): (
                       (-1, _('&About'), _('About this program'), self.OnAbout),
                       (-1, _('&Help'), _('How to use this'), self.OnHelp),
             ),
        }

    def create_menu_bar(self):
        menubar = wx.MenuBar()
        for menu_label, menu_items in self.menu_data.items():
            menubar.Append(self.create_menu(menu_items), menu_label)
        self.SetMenuBar(menubar)

        return menubar

    def create_menu(self, menu_items):
        menu = wx.Menu()
        for each_item in menu_items:
            if isinstance(each_item, dict):
                label = list(each_item.keys())
                assert len(label) == 1
                label = label[0]
                subMenu = self.create_menu(each_item[label])
                menu.AppendMenu(wx.NewId(), label, subMenu)
            else:
                self.create_menu_item(menu, *each_item)

        return menu

    def create_menu_item(self, menu, id, label, status, handler, kind=wx.ITEM_NORMAL):
        if id == wx.ID_SEPARATOR:
            return menu.AppendSeparator()

        menu_item = menu.Append(id, label, status, kind)

        self.Bind(wx.EVT_MENU, handler, menu_item)

        if id == self.ID_RUN:
            self.menu_run = menu_item
        elif id == self.ID_STOP:
            self.menu_stop = menu_item

        return menu_item

    def create_status_bar(self):
        statusbar = self.CreateStatusBar()
        statusbar.SetFieldsCount(2)
        statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_2)
        return statusbar

    def create_tool_bar(self):
        toolbar = self.CreateToolBar()
        tool_map = []
        items = (
            [self.ID_OPEN, _('Load'), 'src/img/open.bmp',
             _('Import a config file'), self.OnOpen],
            # [self.ID_SAVE, 'save.bmp', _('save'),
            #  _('save the config'), self.OnSave],
            [self.ID_SAVEAS, _('Export'), 'src/img/saveas.bmp',
             _('Export a config file'), self.OnSaveAs],
            [None, '', '', '', None],
            [self.ID_TASKBAR, _('iconify'), 'src/img/taskbar.bmp',
             _('Minimize to a taskbar icon'), self.OnHide],
            [self.ID_QUIT, _('Exit'), 'src/img/quit.bmp',
             _('Fully exit program'), self.OnQuit],
            [None, '', '', '', None],
            [self.ID_RUN, _('Run'), 'src/img/run.bmp',
             _('Run QStart'), self.OnRun],
            [self.ID_STOP, _('Pause'), 'src/img/stop.bmp',
             _('Pause QStart'), self.OnStop],
        )

        if not phoenix:  # wx classic
            # Deprecated
            addtool = lambda toolId, label, bitmap, bmpDisabled=wx._gdi.Bitmap,\
                             kind=0, shortHelpString='', longHelpString='',\
                             clientData=None:\
                toolbar.AddLabelTool(id=toolId, label=label, bitmap=bitmap,
                                     bmpDisabled=bmpDisabled, kind=kind,
                                     shortHelp=shortHelpString,
                                     longHelp=longHelpString,
                                     clientData=clientData)
        else:
            addtool = toolbar.AddTool
        for each in items:
            if each[0] is None:
                toolbar.AddSeparator()
                continue
            filename = os.path.join(ROOTDIR, each[2])
            each[2] = wx.Image(filename, wx.BITMAP_TYPE_BMP).ConvertToBitmap()
            tool = addtool(toolId=each[0],
                           label=each[1],
                           bitmap=each[2],
                           bmpDisabled=wx.NullBitmap,
                           shortHelpString=each[3],
                           longHelpString=each[3])
            self.Bind(wx.EVT_MENU, each[-1], tool)
            tool_map.append(tool)

        self.tool_stop = tool_map.pop()
        self.tool_run = tool_map.pop()
        toolbar.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterTool)

        toolbar.Realize()
        return toolbar

    def create_main_sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        for each_child_detail in self.create_child_sizer():
            sizer.Add(*each_child_detail)

        self.SetSizer(sizer)
        return sizer

    def create_child_sizer(self):
        child_sizer = []

        # main keys
        main_key_sizer = wx.BoxSizer(wx.HORIZONTAL)
        BORDER = 5
        label_main_key_1 = wx.StaticText(self, -1, _('Primary Key'))
        label_main_key_2 = wx.StaticText(self, -1, _('Secondary Key'))
        logger.info('key_1: %s, key_2: %s'%(self.key_1, self.key_2))

        self.btn_main_key_1 = wx.Button(self, -1, self.key_info[self.key_1])
        self.btn_main_key_2 = wx.Button(self, -1, self.key_info[self.key_2])

        self.btn_main_key_1.key_id = self.key_1
        self.btn_main_key_2.key_id = self.key_2

        self.Bind(wx.EVT_BUTTON, self.OnHotkeySet, self.btn_main_key_1)
        self.Bind(wx.EVT_BUTTON, self.OnHotkeySet, self.btn_main_key_2)
        self.btn_main_key_1.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterMainkeyButton)
        self.btn_main_key_2.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterMainkeyButton)
        self.btn_main_key_1.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)
        self.btn_main_key_2.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)
        # self.btn_main_key_2.MoveAfterInTabOrder(self.btn_main_key_1)
        # self.btn_main_key_1.MoveAfterInTabOrder(self.btn_main_key_2)

        main_key_sizer.Add(label_main_key_1, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=BORDER)
        main_key_sizer.Add(self.btn_main_key_1, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=BORDER)
        main_key_sizer.Add(label_main_key_2, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=BORDER)
        main_key_sizer.Add(self.btn_main_key_2, proportion=0, flag=wx.ALL|wx.ALIGN_CENTER, border=BORDER)
        child_sizer.append((main_key_sizer, 0, wx.ALL|wx.ALIGN_CENTER, 5))

        # separator
        child_sizer.append((wx.StaticLine(self), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 10))

        # scrollable window
        self.scroll_window = wx.ScrolledWindow(self, -1)
        scroll_window_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_window.SetSizer(scroll_window_sizer)
        self.scroll_window.SetScrollbars(5, 5, 10, 10)

        child_sizer.append((self.scroll_window, 1, wx.EXPAND|wx.ALL^wx.TOP, 15))

        return child_sizer

    def reset_scroll_window(self):
        sizer = self.scroll_window.GetSizer()
        logger.warning('this method not exits and may cause bug')
        # sizer.DeleteWindows()
        sizer.Clear()
        sizer = wx.BoxSizer(wx.VERTICAL)

        for key_id in self.user_info:
            if key_id == '-1':
                continue
            line_sizer = self.create_line_sizer(key_id)
            sizer.Add(line_sizer, 0, wx.EXPAND)

        else:
            line_sizer = self.create_line_sizer(lastline=True)
            sizer.Add(line_sizer, 0, wx.EXPAND)

        self.scroll_window.SetSizer(sizer)
        # sizer.Layout()
        self.scroll_window.FitInside()

    def create_line_sizer(self, key_id='-1', lastline=False, size=(-1, -1)):
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        line_sizer.key_id = key_id

        delete_btn = wx.Button(self.scroll_window, -1, u'×', style=wx.BU_EXACTFIT)

        if lastline:
            id_key = self.ID_LASTLINE_KEY
            id_more = self.ID_LASTLINE_DETAIL
            delete = delete_btn.GetSize()
            delete_btn.Show(False)
            delete_btn.Destroy()
            del delete_btn

            key_name = _('(set)')
            name = ''
            cmd = ''
            style = wx.TE_PROCESS_ENTER

        else:
            id_key = wx.NewId()
            id_more = wx.NewId()

            detail = self.user_info[key_id]
            key_name = self.key_info[key_id]
            name = detail['name']
            cmd = detail['cmd']
            style = 0

            delete = delete_btn
            self.Bind(wx.EVT_BUTTON, self.OnDelete, delete)
            delete.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterDeleteButton)
            delete.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)


        hot_key_name = wx.Button(self.scroll_window, id_key, key_name, style=wx.NO_BORDER)
        cmd_name = wx.TextCtrl(self.scroll_window, -1, name, size=(5, -1), style=style)
        cmd = wx.TextCtrl(self.scroll_window, -1, cmd, style=style)
        detail = wx.Button(self.scroll_window, id_more, u'...', style=wx.BU_EXACTFIT)

        hot_key_name.key_id = key_id
        self.Bind(wx.EVT_BUTTON, self.OnHotkeySet, hot_key_name)
        self.Bind(wx.EVT_BUTTON, self.OnDetail, detail)
        self.Bind(wx.EVT_TEXT, self.OnChangeText, cmd)
        self.Bind(wx.EVT_TEXT, self.OnChangeText, cmd_name)

        hot_key_name.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterKeyButton)
        hot_key_name.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)
        detail.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterDetailButton)
        detail.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)
        cmd_name.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterCmdNameTextbox)
        cmd_name.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)
        cmd.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterCmdTextbox)
        cmd.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWidget)

        if lastline:
            self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterText, cmd)
            self.Bind(wx.EVT_TEXT_ENTER, self.OnEnterText, cmd_name)

        line_sizer.Add(hot_key_name)
        line_sizer.Add(cmd_name, 1, wx.EXPAND)
        line_sizer.Add(cmd, 5, wx.EXPAND)
        line_sizer.Add(detail)
        line_sizer.Add(delete)

        return line_sizer

    def create_about_dlg(self):
        title = _("About QStart")
        dlg = AboutBox(self, -1, title)
        dlg.SetTitleIcon(os.path.join(ROOTDIR, self.ICO_TITLE),
                         wx.BITMAP_TYPE_PNG)
        dlg.SetCenterIcon(os.path.join(ROOTDIR, self.ICO),
                          wx.BITMAP_TYPE_PNG,
                          (80, 80))
        dlg.SetVersion(self.VERSION)
        dlg.SetName(_('QStart'))
        dlg.SetCopyright(_('\u00a9 2013 - 2015 TylerTemp'))
        dlg.SetDescription(_('QStart helps you open a file/program or '
                             'run a command by pressing 3 keys.\n'
                             'You can also pause it in toolbar button, menu '
                             'or popup menu of taskbar icon'))
        dlg.SetWebsite('TODO: add website')

        # email
        text = wx.StaticText(dlg, -1, label='TylerTemp')
        logger.warning('style wx.HL_DEFAULT_STYLE is gone '
                       'and may cause unexpected result')
        link = HyperlinkCtrl(dlg, label=_('email: tylertempdev@gmail.com'),
                             url='tylertempdev@gmail.com')  # ,
                             # style=wx.HL_DEFAULT_STYLE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text)
        sizer.Add(link)  # , 0, wx.ALIGN_CENTER)
        dlg.AddDetail(_('Author'), sizer, True)

        # license link
        text = wx.StaticText(
            dlg,
            -1,
            label=_('QStart is a free/libre and open source software under '
                    'GPLv3 license.'))
        logger.warning('style wx.HL_DEFAULT_STYLE is gone '
                       'and may cause unexpected result')
        link = HyperlinkCtrl(
            dlg,
            label=_('GPLv3 license'),
            url='http://www.gnu.org/licenses/gpl-3.0.txt')  # ,
            # style=wx.HL_DEFAULT_STYLE)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text)
        sizer.Add(link, 0, wx.ALIGN_CENTER)
        dlg.AddDetail(_('License'), sizer, True)
        # dlg.AddDetail(_('disclaimer'), '')
        return dlg

    def user_data(self, abs_file):
        default = [
            '-1',
            '-1',
            {'-1': {'cmd': None, 'flag': True, 'key': '', 'name': ''}}]

        if os.path.exists(abs_file):
            logger.info('load user data from %s', abs_file)
            self.user_info_file = open(abs_file, 'r+', encoding='utf-8')
            raw = self.user_info_file.read()
            if not raw:
                logger.info('empty, return default')
                return default
            cfg = json.loads(raw)
            key_1 = cfg.get('key_1', '-1')
            key_2 = cfg.get('key_2', '-1')
            info = cfg.get('info', default[-1])
            return (key_1, key_2, info)

        logger.info('user data not exists(%s)', abs_file)
        self.user_info_file = open(abs_file, 'w+', encoding='utf-8')
        return default

    def key_data(self):
        abs_file = os.path.join(ROOTDIR, self.KEY_INFO)
        with open(abs_file, 'r', encoding='utf-8') as f:
            dic = json.load(f)

        reset_key = set(self.user_info.keys()).difference(dic.keys())
        for each_id in reset_key:
            dic[each_id] = self.user_info[each_id]['key']
        return dic

    def key_manager(self, event):

        logger.debug('get key %s', event.KeyID)
        key_id = str(event.KeyID)
        # if not self.IS_RUN:
        #     return True
        has_key = len(self.KEY_LIST)

        if has_key == 0 and key_id == self.key_1:
            self.KEY_LIST.append(self.key_1)
            return True
        if has_key == 1:
            if key_id == self.key_2:
                self.KEY_LIST.append(self.key_2)
            return True

        if (has_key == 2) and(key_id in self.user_info):
            flag = self.user_info[key_id]['flag']
            cmd = self.user_info[key_id]['cmd']

            if flag:
                subprocess.Popen(args=cmd, shell=True)
            else:
                os.startfile(cmd)

            self.KEY_LIST=[]
        return True

    def key_up(self, event):
        logger.debug('key up, clean')
        self.KEY_LIST[:] = ()  # py2 list has no list.clear()
        return True

    def change_key_handler(self, key_id, key_name, widget):
        logger.debug('change key handler')
        self.SetFocus()
        orl_key_id = widget.key_id
        logger.debug('original key id: %s', orl_key_id)

        if widget is self.btn_main_key_1:
            logger.debug('set primary key')
            self.key_1 = key_id
            self.btn_main_key_1.SetLabel(key_name)
            self.btn_main_key_1.key_id = key_id
            return

        if widget is self.btn_main_key_2:
            logger.debug('set secondary key')
            self.key_2 = key_id
            self.btn_main_key_2.SetLabel(key_name)
            self.btn_main_key_2.key_id = key_id
            return

        if widget.GetId() == self.ID_LASTLINE_KEY:
            if key_id in self.user_info:
                wx.MessageBox(
                    _('Repeated key:\nID: %s\n alias: %s') % (key_id, key_name),
                    _('Error'),
                    style=wx.OK| wx.ICON_ERROR)
                return
            self.user_info[key_id] = {
                "cmd": "",
                "flag": True,
                "key": key_name,
                "name": "",
            }
            line_sizer = self.create_line_sizer(key_id = key_id)
            line_sizer.key_id = key_id
            sizer = self.scroll_window.GetSizer()
            sizer.Insert(len(sizer.GetChildren())-1, line_sizer, 0, wx.EXPAND)
            sizer.Layout()
            self.scroll_window.FitInside()
            return


        if (key_id != orl_key_id) and key_id in self.user_info:
            wx.MessageBox(
                _('Repeated key:\nID: %s\nalias: %s') % (key_id, key_name),
                _('Error'),
                style=wx.OK| wx.ICON_ERROR)
            return

        widget.SetLabel(key_name)
        widget.key_id = key_id
        self.key_info[key_id] = key_name

        if orl_key_id in self.user_info:
            value = self.user_info.pop(orl_key_id)
            self.user_info[key_id] = value

    def change_detail_handler(self, key_id, key_name, cmd, cmd_name, flag, line_sizer):
        self.SetFocus()
        orl_key_id = line_sizer.key_id

        sizer_item_list = line_sizer.GetChildren()
        button_key = sizer_item_list[0].GetWindow()

        if button_key.GetId() == self.ID_LASTLINE_KEY:
            if key_id in self.user_info:
                wx.MessageBox(
                    _('Repeated key:\nID: %s\nalias: %s') % (key_id, key_name),
                    _('Error'),
                    style=wx.OK| wx.ICON_ERROR)
                return
            self.user_info[key_id] = {
                "cmd": cmd,
                "flag": flag,
                "key": key_name,
                "name": cmd_name,
            }
            line_sizer = self.create_line_sizer(key_id = key_id)
            line_sizer.key_id = key_id
            sizer = self.scroll_window.GetSizer()
            sizer.Insert(len(sizer.GetChildren())-1, line_sizer, 0, wx.EXPAND)
            sizer.Layout()
            self.scroll_window.FitInside()
            return

        if (key_id != orl_key_id) and (key_id in self.user_info):
            wx.MessageBox(
                _('Repeated key:\nID: %s\nalias: %s') % (key_id, key_name),
                _('Error'),
                style=wx.OK| wx.ICON_ERROR)
            return

        self.user_info[key_id] = {
            "cmd": cmd,
            "flag": flag,
            "key": key_name,
            "name": cmd_name,
        }

        button_key.key_id = key_id
        line_sizer.key_id = key_id
        button_key.SetLabel(key_name)
        sizer_item_list[1].GetWindow().SetValue(cmd_name)
        sizer_item_list[2].GetWindow().SetValue(cmd)

    def SetRun(self, state):
        self.IS_RUN = bool(state)

        a = (self.tool_run, self.tool_stop)[self.IS_RUN]
        self.toolbar.RemoveTool(self.ID_RUN)
        self.toolbar.RemoveTool(self.ID_STOP)
        if phoenix:  # wx phoenix
            addtool = self.toolbar.AddTool
        else:  # wx classic
            # Deprecated in phoenix
            addtool = lambda toolId, bitmap, label, shortHelp:\
                self.toolbar.AddSimpleTool(toolId, label, bitmap, shortHelp)
        addtool(a.GetId(), a.GetShortHelp(), a.GetNormalBitmap(), a.GetLongHelp())
        self.toolbar.Realize()
        if state:
            self.key_obj.HookKeyboard()
        else:
            self.key_obj.UnhookKeyboard()
        self.menu_run.Check(self.IS_RUN)
        self.run_info()

        return self.IS_RUN

    def run_info(self):
        if self.IS_RUN:
            info = _('Running')
        else:
            info = _('Paused')
        self.statusbar.SetStatusText(info, self.statusbar.GetFieldsCount() - 1)

    def OnIconStartup(self, evt, icon):
        evt.GetEventObject().FindItem(evt.GetId())[0].Check(True)
        self.start_on_icon = icon

    def OnChangeLang(self, evt, code):
        _id = evt.GetId()
        item = evt.GetEventObject().FindItem(_id)[0]
        item.Check(True)
        label = item.GetItemLabelText()
        logger.debug('%s(id: %s)', label, _id)

        logger.info('change language: %s -> %s', self.current_lang, code)
        self.current_lang = code
        translator.lang = code

        if (self.INIT_LANG != code and
                set((self.INIT_LANG, code)).difference((None, 'en_US'))):
            wx.MessageBox(
                _('Please restart QStart to change to language %s') % label,
                _('Restart QStart Required'),
                style=wx.OK| wx.ICON_INFORMATION)

    def OnChangeText(self, event):
        sizer = event.GetEventObject().GetContainingSizer()
        btn = sizer.GetChildren()[0].GetWindow()
        name = sizer.GetChildren()[1].GetWindow()
        cmd = sizer.GetChildren()[2].GetWindow()
        first_id = btn.GetId()

        if first_id != self.ID_LASTLINE_KEY:
            key_id = btn.key_id
            detail = self.user_info[key_id]
            detail['cmd'] = cmd.GetValue()
            detail['name'] = name.GetValue()

        event.Skip()

    def OnEnterText(self, event):
        this_sizer = event.GetEventObject().GetContainingSizer()
        name = this_sizer.GetChildren()[1].GetWindow()
        cmd  = this_sizer.GetChildren()[2].GetWindow()

        self.user_info['-1']={
            "cmd":cmd.GetValue(),
            "flag": True,
            "key": '',
            "name": name.GetValue()
        }
        name.SetValue('')
        cmd.SetValue('')

        line_sizer = self.create_line_sizer('-1')
        sizer = self.scroll_window.GetSizer()
        sizer.Insert(len(sizer.GetChildren())-1, line_sizer, 0, wx.EXPAND)
        sizer.Layout()
        self.scroll_window.FitInside()
        event.Skip()

    def OnEnterMainkeyButton(self, event):
        btn = event.GetEventObject()
        if btn is self.btn_main_key_2:
            info = _('Change the secondary key')
        else:
            info = _('Change the primary key')

        name = btn.GetLabel()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_3)
        self.statusbar.SetStatusText(info, 0)
        self.statusbar.SetStatusText(_('Name: %s ID: %s') % (name, btn.key_id),
                                     1)
        self.run_info()
        event.Skip()

    def OnEnterCmdNameTextbox(self, event):
        name = event.GetEventObject().GetValue()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_3)
        if name:
            self.statusbar.SetStatusText(_('Change the name of this command'),
                                         0)
            self.statusbar.SetStatusText(name,1)
        else:
            self.statusbar.SetStatusText(_('Add a name for this command'), 0)
            self.statusbar.SetStatusText('',1)
        self.run_info()
        event.Skip()

    def OnEnterCmdTextbox(self, event):
        sizer_items = event.GetEventObject().GetContainingSizer().GetChildren()
        btn = sizer_items[0].GetWindow()
        key_id = btn.key_id
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_3)
        if key_id in self.user_info:
            flag = self.user_info[key_id]['flag']
            cmd = self.user_info[key_id]['cmd'] or ''
        else:
            flag = True
            cmd = ''
        self.statusbar.SetStatusText(_(('Change Command', 'Change File')[flag]),
                                     0)
        self.statusbar.SetStatusText(cmd, 1)
        self.run_info()
        event.Skip()

    def OnEnterKeyButton(self, event):
        btn = event.GetEventObject()
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_2)
        if btn.GetId() == self.ID_LASTLINE_KEY:
            self.statusbar.SetStatusText(_('Set a hotkey and add a new record'),
                                         0)
        elif btn.key_id == '-1':
            self.statusbar.SetStatusText(_('Set a hotkey'), 0)
        else:
            self.statusbar.SetFieldsCount(3)
            self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_3)
            self.statusbar.SetStatusText(_('Change the hotkey'), 0)
            self.statusbar.SetStatusText(
                _('Name: %s ID: %s') % (btn.GetLabel(), btn.key_id), 1)
        self.run_info()
        event.Skip()

    def OnEnterDetailButton(self, event):
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_2)
        self.statusbar.SetStatusText(_('Set detail infomation'), 0)
        self.run_info()
        event.Skip()

    def OnEnterDeleteButton(self, event):
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_2)
        self.statusbar.SetStatusText(_('Delete this line'), 0)
        self.run_info()

        event.Skip()

    def OnEnterTool(self, event):
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_2)
        self.statusbar.SetStatusText('', 0)
        self.run_info()
        event.Skip()

    def OnLeaveWidget(self, event):
        # self.statusbar.SetStatusText(u'', 0)
        # self.statusbar.SetFieldsCount(2)
        # self.statusbar.SetStatusWidths(self.STATUSBAR_WIDTH_2)
        # self.run_info()
        event.Skip()

    # menu/tool event handler
    def OnHotkeySet(self, event):
        logger.debug('to set hotkey')
        obj = event.GetEventObject()

        key_id = obj.key_id
        key_name = self.key_info[key_id]

        self.catch_key_frame.reset_frame(
            key_id, self.key_manager, self.change_key_handler, obj)
        self.catch_key_frame.Show(True)
        self.catch_key_frame.CenterOnParent()
        self.catch_key_frame.catch_key()
        self.detail_frame.Show(False)
        self.catch_key_frame.SetFocus()

    def OnOpen(self, event):
        if hasattr(event, 'GetFiles'):
            abs_file = os.path.abspath(event.GetFiles()[0])
        else:
            abs_file = wx.FileSelector(_('Select a config file'),
                                       ROOTDIR, self.USER_INFO)
        if abs_file:
            try:
                self.key_1, self.key_2, self.user_info = \
                    self.user_data(abs_file)
            except Exception as e:
                wx.MessageBox(_('Unavailable file format:\n') + str(e),
                              _('Failed'),
                              style=wx.OK| wx.ICON_ERROR)
            else:

                self.btn_main_key_1.key_id = self.key_1
                self.btn_main_key_2.key_id = self.key_2

                label_1 = self.key_info.get(self.key_1, '')
                label_2 = self.key_info.get(self.key_2, '')
                if not label_1:
                    label_1 = self.user_info.get(self.key_1, '')
                if not label_2:
                    label_2 = self.user_info.get(self.key_2, '')
                self.btn_main_key_1.SetLabel(label_1)
                self.btn_main_key_2.SetLabel(label_2)
                self.reset_scroll_window()

    def OnSave(self, event, file_name=None):
        if file_name is None:
            file_name = os.path.join(ROOTDIR, self.USER_INFO)

        info = dict(self.user_info)
        if '-1' in info:
            info.pop('-1')
        key_1 = self.key_1
        key_2 = self.key_2
        current_lang = self.current_lang
        start_on_icon = self.start_on_icon

        save = {}
        if key_1 != '-1':
            save['key_1'] = key_1
        if key_2 != '-1':
            save['key_2'] = key_2
        if info:
            save['info'] = info
        if current_lang is not None:
            save['lang'] = current_lang
        if start_on_icon:
            save['start_on_icon'] = True

        with open(file_name, 'w', encoding='utf-8') as f:
            if save:
                logger.info('config saved to %s', file_name)
                json.dump(save, f, sort_keys=True, indent=4)
            else:  # just truncate the file
                logger.info('nothing to save')

    def OnSaveAs(self, event):
        abs_file = wx.FileSelector(_('Save the config'),
                                   ROOTDIR,
                                   self.USER_INFO,
                                   flags=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if abs_file:
            self.OnSave(event, abs_file)

    def OnQuit(self, event):
        ctypes.windll.user32.PostQuitMessage(0)
        self.OnSave(event)
        self.key_obj.UnhookKeyboard()
        self.user_info_file.close()
        self.about_dlg.Destroy()
        self.taskbar_icon.Destroy()
        self.detail_frame.Destroy()
        self.catch_key_frame.Destroy()

        self.Destroy()
        return

    def OnAbout(self, event):
        self.about_dlg.ShowModal()
        return

    def OnHelp(self, event):
        return

    # button event handler
    def OnDelete(self, event):
        sizer = self.scroll_window.GetSizer()
        sub_sizer = event.GetEventObject().GetContainingSizer()
        sub_sizer.Clear(True)
        sizer.Layout()
        self.scroll_window.FitInside()

        if sub_sizer.key_id == '-1':
            self.user_info['-1'] = {
                'cmd':'',
                'flag': True,
                'key': '',
                'name': '',
            }
        else:
            self.user_info.pop(sub_sizer.key_id)

    def OnDetail(self, event):
        sizer = event.GetEventObject().GetContainingSizer()
        key_id = sizer.key_id
        key_name = sizer.GetChildren()[0].GetWindow().GetLabel()
        cmd      = sizer.GetChildren()[1].GetWindow().GetValue()
        cmd_name = sizer.GetChildren()[2].GetWindow().GetValue()
        flag     = True
        if key_id in self.user_info and key_id != '-1':
            key_name = self.user_info[key_id]['key']
            cmd      = self.user_info[key_id]['cmd']
            cmd_name = self.user_info[key_id]['name']
            flag     = self.user_info[key_id]['flag']

        self.detail_frame.reset_frame(key_id, key_name, cmd, cmd_name, flag, sizer, self.change_detail_handler)
        self.detail_frame.Show(True)
        self.detail_frame.CenterOnParent()
        self.catch_key_frame.Show(False)
        self.detail_frame.SetFocus()

    def OnHide(self, event):
        self.detail_frame.Show(False)
        self.catch_key_frame.Show(False)
        if not self.IS_SHOW:
            return
        if not self.IsIconized():
            self.Iconize(True)
        if self.IsShown():
            self.Show(False)

        self.Raise()
        self.IS_SHOW = False

    def OnShow(self, event):
        if self.IS_SHOW:
            return
        if self.IsIconized():
            self.Iconize(False)
        if not self.IsShown():
            self.Show(True)
        self.Raise()
        self.IS_SHOW = True

    def OnRun(self, event):
        self.SetRun(True)

    def OnStop(self, event):
        self.SetRun(False)
