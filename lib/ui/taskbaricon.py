from __future__ import unicode_literals
import wx
import win32gui
import logging
try:
    from wx.adv import TaskBarIcon, EVT_TASKBAR_LEFT_UP
except ImportError:
    from wx import TaskBarIcon, EVT_TASKBAR_LEFT_UP

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
    LIBDIR = os.path.normpath(os.path.join(__file__, '..', '..', '..'))

sys.path.insert(0, LIBDIR)
from lib.tool.translate import Translate
sys.path.pop(0)

logger = logging.getLogger('ui.taskbaricon')
_ = Translate().translate


class TaskBarIcon(TaskBarIcon):

    FILE = 'src/img/taskbar.ico'

    ids = [wx.NewId() for i in range(5)]

    def __init__(self, frame):
        super(TaskBarIcon, self).__init__()
        self.frame = frame
        self.SetIcon(
            wx.Icon(name=os.path.join(ROOTDIR, self.FILE),
                    type=wx.BITMAP_TYPE_ICO),
            _('Qstart'))

        self.Bind(EVT_TASKBAR_LEFT_UP, self.OnTaskBarLeftClick)
        self.Bind(wx.EVT_MENU, self.frame.OnShow, id=self.ids[0])
        self.Bind(wx.EVT_MENU, self.frame.OnHide, id=self.ids[1])
        self.Bind(wx.EVT_MENU, self.frame.OnRun, id=self.ids[2])
        self.Bind(wx.EVT_MENU, self.frame.OnStop, id=self.ids[3])
        self.Bind(wx.EVT_MENU, self.frame.OnQuit, id=self.ids[4])

        self.ShowBalloon(_('Started'), _('Click the icon to show/hide window'),
                         msec=0, flags=wx.ICON_INFORMATION)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        show = menu.Append(self.ids[0], _('Show'),
                           _('Show the window'), wx.ITEM_RADIO)
        hide = menu.Append(self.ids[1], _('Hide'),
                           _('Hide the window'), wx.ITEM_RADIO)
        menu.AppendSeparator()
        run = menu.Append(self.ids[2], _('Run'),
                          _('Trun on QStart Hotkey'), wx.ITEM_RADIO)
        stop = menu.Append(self.ids[3], _('Pause'),
                           _('Trun off QStart Hotkey'), wx.ITEM_RADIO)
        menu.AppendSeparator()
        quit = menu.Append(self.ids[4], _('Exit'), _('Fully exit program'))

        run.Check(self.frame.IS_RUN)
        stop.Check(not self.frame.IS_RUN)
        show.Check(self.frame.IS_SHOW)
        hide.Check(not self.frame.IS_SHOW)

        return menu

    def OnTaskBarLeftClick(self, event):

        # if self.frame.IsIconized() and (not self.frame.IsShown()):
        if not self.frame.IsShown():
            logger.debug('to show')
            self.frame.OnShow(event)
            self.frame.SetFocus()
        else:
            logger.debug('to hide')
            self.frame.OnHide(event)
        return

    def ShowBalloon(self, title, text, msec=0, flags=0):
        """
        Show Balloon tooltip
         @param title - Title for balloon tooltip
         @param msg   - Balloon tooltip text
         @param msec  - Timeout for balloon tooltip, in milliseconds
         @param flags - one of wx.ICON_INFORMATION, wx.ICON_WARNING,
                        wx.ICON_ERROR
        """
        if self.IsIconInstalled():
            try:
                self.__SetBalloonTip(self.icon.GetHandle(), title, text, msec,
                                     flags)
            except Exception as e:
                logger.error(e)

    def __SetBalloonTip(self, hicon, title, msg, msec, flags):

        # translate flags
        infoFlags = 0

        if flags & wx.ICON_INFORMATION:
            infoFlags |= win32gui.NIIF_INFO
        elif flags & wx.ICON_WARNING:
            infoFlags |= win32gui.NIIF_WARNING
        elif flags & wx.ICON_ERROR:
            infoFlags |= win32gui.NIIF_ERROR

        # Show balloon
        lpdata = (self.__GetIconHandle(),  # hWnd
                  99,  # ID
                  # flags: Combination of NIF_* flags
                  win32gui.NIF_MESSAGE | win32gui.NIF_INFO | win32gui.NIF_ICON,
                  # CallbackMessage: Message id to be pass to hWnd
                  # when processing messages
                  0,
                  hicon,  # hIcon: Handle to the icon to be displayed
                  '',  # Tip: Tooltip text
                  msg,  # Info: Balloon tooltip text
                  # Timeout: Timeout for balloon tooltip, in milliseconds
                  msec,
                  title,  # InfoTitle: Title for balloon tooltip
                  infoFlags  # InfoFlags: Combination of NIIF_* flags
                  )
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, lpdata)

        # Hack: because we have no access to the real CallbackMessage value
        self.SetIcon(self.icon, self.tooltip)

    def __GetIconHandle(self):
        """
        Find the icon window.
        This is ugly but for now there is no way to find this window
        directly from wx
        """
        if not hasattr(self, "_chwnd"):
            try:
                for handle in wx.GetTopLevelWindows():
                    if handle.GetWindowStyle():
                        continue
                    handle = handle.GetHandle()
                    if len(win32gui.GetWindowText(handle)) == 0:
                        self._chwnd = handle
                        break
                if not hasattr(self, "_chwnd"):
                    raise Exception
            except:
                raise Exception("Icon window not found")
        return self._chwnd

    def SetIcon(self, icon, tooltip=""):
        self.icon = icon
        self.tooltip = tooltip
        super(TaskBarIcon, self).SetIcon(icon, tooltip)

    def RemoveIcon(self):
        self.icon = None
        self.tooltip = ""
        wx.TaskBarIcon.RemoveIcon(self)
