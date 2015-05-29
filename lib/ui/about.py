# coding:utf-8
from __future__ import unicode_literals
# about_frame.py -- a AboutBox
# -rem gAMA -rem cHRM -rem iCCP -rem sRGB About.png About2.png
'''It's a about box that center the icon at the center of the dialog
the API is different from the standard wx.AboutBox
Note that any "Set*" method should only called one time.
suggest order: [SetCenterIcon], SetVersion, SetName, SetCopyright,
SetDescription , SetWebsite, Add*'''
import warnings
import wx
from wx.html import HtmlWindow
try:
    from wx.adv import HyperlinkCtrl
except ImportError:
    from wx import HyperlinkCtrl

class AboutBox(wx.Dialog):
    BORDER = 15
    """an about box to show any information about your porgram"""

    def __init__(self, parent=None, id=-1, title=wx.EmptyString,
        pos=wx.DefaultPosition, size=wx.DefaultSize,
        # style=wx.FRAME_TOOL_WINDOW| wx.FRAME_NO_TASKBAR | wx.CAPTION
        #  | wx.CLOSE_BOX | wx.RESIZE_BORDER | wx.MINIMIZE_BOX,
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.FRAME_NO_TASKBAR,
         # | wx.THICK_FRAME,
        name=wx.DialogNameStr):
        '''Note that if title is wx.EmptyString and the parent has the attr "Title",
        the title will be "About "+getattr(parent, "Title")'''

        if title is wx.EmptyString and hasattr(parent, 'Title'):
            title = 'About %s' %getattr(parent, 'Title')

        super(AboutBox, self).__init__(parent=parent, id=id, title=title,
                                       pos=pos, size=size, style=style,
                                       name=name)
        self.SetBackgroundColour('WHITE')
        # format: {btn_id: context_size_item}
        self._btn_detail = dict()
        self._sizer = wx.BoxSizer(wx.VERTICAL)

        self._icon = None
        if hasattr(parent, 'Title'):
            self._name = getattr(parent, 'Title')
        else:
            self._name = ''
        self._has_name = False
        self._version = ''
        self._copyright = ''
        self._description = ''
        self._website = ''
        self.SetSizer(self._sizer)

    def SetCenterIcon(self, file_name, file_type=wx.BITMAP_TYPE_ANY, size = wx.DefaultSize):
        '''SetCenterIcon(str file_name, long file_type=BITMAP_TYPE_ANY) -> SizerItem
        Set the icon of the program
        which will be showed at the conter of the dialog
        return the SizerItem of StaticBitmap'''
        img = wx.Image(file_name, file_type)
        if isinstance(size, tuple):
            size = wx.Size(*size)
        if size != wx.DefaultSize:
            w = size.width
            h = size.height
            img = img.Scale(w, h)
        self._icon = img
        img_box = wx.StaticBitmap(self, -1, wx.Bitmap(img, file_type))
        sizer_item = self._sizer.Insert(0, img_box, 0, wx.ALIGN_CENTER | wx.FIXED_MINSIZE)
        return sizer_item

    def SetTitleIcon(self, file_name, file_type=wx.BITMAP_TYPE_ANY):
        '''SetTitleIcon(str file_name, long file_type=BITMAP_TYPE_ANY) ->None
        Set the Icon of the dialog at the title.
        Note that you can still call SetIcon(wxIcon) to set icon by yourself
        It will not set the center icon showed.If needed, you can call "SetCenterIcon()"'''
        icon = wx.Icon(file_name, file_type)
        return super(self.__class__, self).SetIcon(icon)

    def SetName(self, name, font_size = 15):
        '''SetName(str name) -> SizerItem
        Set the name of your program. Call after "SetVersion" or the version will not work.
        Note that it does not change the title of the program
        and the displayed name is "name"+"version"
        You should never change the name later or the center style will disappear.'''
        name = name.strip()
        self._name = name
        self._has_name = True
        index = 0
        if self._version:
            name = '%s %s'%(name, self._version)
        if self._icon is not None:
            index += 1
        # name = u'\xa9 2006 by ....'
        name_box = wx.StaticText(self, label=name, style=wx.ALIGN_CENTER)
        name_box.SetFont(wx.Font(font_size, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        sizer_item = self._sizer.Insert(index, name_box, 0, wx.ALIGN_CENTER | wx.FIXED_MINSIZE | wx.EXPAND)

        return sizer_item
    def GetName(self):
        '''GetName -> str'''
        return self._name

    def SetVersion(self, version):
        '''SetVersion(self, str version) -> str
        Set the version of the program. Call this before "SetName" or it will not work.
        return version.strip()'''
        self._version = version.strip()
        return self._version
    def GetVersion(self):
        '''GetVersion() -> str
        return the version of the program
        return empty string if not set by calling SetVersion.'''
        return self._version

    def SetCopyright(self, copyright, font_size=3):
        '''SetCopyright(self, str copyright, int font_size=3) -> SizerItem
        It will replace the "(c)"(small letter) into the offical sign'''
        htm = HtmlWindow(self, style=wx.html.HW_SCROLLBAR_NEVER, size=(-1, 40))
        self._copyright = copyright
        copyright =  copyright.replace('(c)', '</font><font size="%s">&copy;</font><font size="%s">'%(font_size+2, font_size))
        copyright = '<font size="%s">%s</font>'%(font_size, copyright)
        htm.SetPage('<html><body><center>%s</center><body></html>'%copyright)
        # self._sizer.Add(htm, 0, wx.EXPAND)
        index = 0
        if self._icon is not None:
            index += 1
        if self._has_name is True:
            index += 1
        sizer_item = self._sizer.Insert(index, htm, 0, wx.EXPAND| wx.ALIGN_CENTER)

        return sizer_item
    def GetCopyright(self):
        '''GetCopyright() -> str'''
        return self._copyright

    def SetDescription(self, description):
        '''SetDescription(str description) -> SizerItem
        the description will show directly.'''
        self._description = description

        desc = wx.StaticText(self, label=description)
        index = 0
        if self._icon is not None:
            index += 1
        if self._has_name:
            index += 1
        if self._copyright:
            index += 1
        sizer_item = self._sizer.Insert(index, desc, 0, wx.ALIGN_CENTER | wx.FIXED_MINSIZE | wx.ALL, self.BORDER)

        return sizer_item
    def GetDescription(self):
        '''GetDescription() -> str'''
        return self._description

    def SetWebsite(self, link, label = None):
        '''SetWebsite(self, str link, str lable=None) -> SizerItem
        Set the website of your program
        if label is None, then it will be the same as link'''
        self._website = link
        if label is None:
            label = link

        warnings.warn('wx.HL_DEFAULT_STYLE is gone and '
                      'may cause unexpected result')
        linker = HyperlinkCtrl(self, label=label, url=link)  # , style=wx.HL_DEFAULT_STYLE)

        index = 0
        if self._icon is not None:
            index += 1
        if self._has_name is True:
            index += 1
        if self._copyright:
            index += 1
        if self._description:
            index += 1
        sizer_item = self._sizer.Insert(index, linker, 0, wx.ALIGN_CENTER | wx.FIXED_MINSIZE)

        return sizer_item
    def GetWebsite(self):
        '''GetWebsite() -> str'''
        return self._website

    def AddDetail(self, label, context, force=False):
        '''AddDetail(str label, str context, force=False) -> None
        Add a button with given label(">>" and "<<" at the end means show or hide), a static line
        then add a statictext of given context.
        make force=True then you can pass an object(even a sizer) as context'''
        btn = wx.Button(self, -1, label='%s >>'%label, style=wx.BU_EXACTFIT)
        line = wx.StaticLine(self, style=wx.LI_HORIZONTAL)
        if force is False:
            context = wx.StaticText(self, -1, label=context)

        self.Bind(wx.EVT_BUTTON, self._OnButton, btn)

        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        line_sizer.Add(btn, 0)
        line_sizer.Add(line, 1, wx.ALIGN_CENTER_VERTICAL)

        self._sizer.Add(line_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, self.BORDER)
        sizer_item = self._sizer.Add(context, 0, wx.ALIGN_LEFT| wx.LEFT | wx.RIGHT, self.BORDER)
        self._btn_detail[btn.GetId()] = sizer_item
        sizer_item.Show(False)


    def _OnButton(self, event):
        btn = event.GetEventObject()
        btn_complex_label = btn.GetLabel()
        btn_id = btn.GetId()

        btn_label, btn_state = btn_complex_label[:-3], btn_complex_label[-3:]
        context = self._btn_detail[btn_id]
        if btn_state.endswith('>>'):
            context.Show(True)
            btn.SetLabel('%s <<'%btn_label)
        else:
            context.Show(False)
            btn.SetLabel('%s >>'%btn_label)
        self._sizer.Layout()
        size = self.GetSize()
        h, w = size.height, size.width
        self.Fit()
        new_size = self.GetSize()
        nh, hw = new_size.height, new_size.width
        # if nh <= h:
        #     nh = h
        self.SetSize((w, nh))

    def ShowModal(self):
        if not self.FindWindowById(wx.ID_OK):
            btn_ok = wx.Button(self, wx.ID_OK, label='OK')
            self._sizer.Add(wx.Size(-1, -1), 1)
            self._sizer.Add(btn_ok, 0, wx.ALL | wx.ALIGN_RIGHT | wx.ALIGN_BOTTOM, self.BORDER)
        self._sizer.Layout()
        self.Fit()
        super(self.__class__, self).ShowModal()


if __name__ == '__main__':
    desc  = '''test test test'''
    app = wx.App(False)
    frame = wx.Frame(None, title='Test')
    dlg = AboutBox(frame)
    dlg.SetTitleIcon('main.ico', wx.BITMAP_TYPE_ICO)
    dlg.SetCenterIcon('About.png', wx.BITMAP_TYPE_ANY, (80, 80))
    dlg.SetVersion('1.0.0.1')
    dlg.SetCopyright('(c) Tyler Temp 2013 - 1024')
    dlg.SetName('QStart')
    dlg.SetDescripiton(desc)
    dlg.SetWebsite('http://www.google.com', 'Google')
    dlg.AddDetail('Name', 'Tyler')
    dlg.AddDetail('User', 'You \n Me \n He')
    dlg.ShowModal()
    dlg.Destroy()
    frame.Destroy()
    app.MainLoop()
