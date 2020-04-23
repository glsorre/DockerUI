from src.dockerui.container import Container

import time

import docker
import rx

from rx.subject import Subject
from rx.scheduler.mainloop import WxScheduler

import wx
import wx.lib.inspection
import wx.xrc

RSRC_FILE = "src/dockerui/app.xrc"
RSRC_FRAMENAME = "mainFrame"

client = docker.from_env()

class DockerUI(wx.App):
    view_list = False

    def OnInit(self):
        self.res = wx.xrc.XmlResource.Get()
        self.res.LoadFile(RSRC_FILE)
        self.containers = Subject()
        self.images = Subject()
        self.render()
        self.toolbar()
        self.menu()
        return True
    
    def render(self):
        self.frame = self.res.LoadFrame(None, RSRC_FRAMENAME)
        self.SetTopWindow(self.frame)
        self.frame.SetMinSize((400, 200))
        self.frame.SetSize((600, 600))
        self.frame.Centre(wx.BOTH)
        self.notebook = wx.xrc.XRCCTRL(self.frame, "mainNotebook")
        self.window = wx.xrc.XRCCTRL(self.frame, "containersWindow")
        self.panel = wx.xrc.XRCCTRL(self.frame, "containersPanel")
        self.page = wx.xrc.XRCCTRL(self.frame, "containersPage")
        self.panel.wrap_sizer = wx.WrapSizer()
        self.window.SetScrollRate(5,5)
        self.frame.Bind(wx.EVT_SIZE, self.on_size)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE))
        self.frame.Show()

    def menu(self):
        menu_bar  = wx.MenuBar()
        help_menu = wx.Menu()

        help_menu.Append(wx.ID_ABOUT, "&About")
        menu_bar.Append(help_menu, "&Help")

        self.frame.SetMenuBar(menu_bar)
        #self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)

    def toolbar(self):
        self.toolbar = wx.ToolBar(self.frame)
        self.text_ctrl = wx.TextCtrl(self.toolbar)
        self.text_ctrl.SetHint("Search")  

        bmp = wx.ArtProvider.GetBitmap(wx.ART_UNDO)

        self.frame.SetToolBar(self.toolbar)

        self.toogle_list_btn = self.toolbar.AddCheckTool(wx.ID_ANY, 'Toogle list view', bmp)
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddControl(self.text_ctrl)
        refresh = self.toolbar.AddTool(wx.ID_ANY, 'Refresh', bmp)

        self.frame.Bind(wx.EVT_TEXT, self.filter, self.text_ctrl)
        self.frame.Bind(wx.EVT_BUTTON, self.filter, refresh)
        self.frame.Bind(wx.EVT_TOOL, self.toogle_list, self.toogle_list_btn)

        self.toolbar.Realize()

    def update(self):
        self.panel.SetSizer(self.panel.wrap_sizer)
        self.frame.SendSizeEvent()

    def on_size(self, event):
        #size = self.frame.GetSize()
        #vsize = self.frame.GetVirtualSize()
        # if self.panel.GetSizer() is not self.panel.wrap_sizer:
        self.panel.SetSizer(self.panel.wrap_sizer)
        #self.notebook.SetVirtualSize((size[0], vsize[1]))
        self.panel.SetMaxSize(self.panel.GetParent().GetParent().GetSize())
        self.panel.SetSize(self.panel.GetParent().GetParent().GetSize())
        self.panel.Centre()
        event.Skip()

    def filter(self, event):    
        text = self.text_ctrl.GetValue()
        if text:
            result = list(filter(lambda c: c.name.startswith(text), client.containers.list(True)))
            self.containers.on_next(result)
        else:
            self.containers.on_next(client.containers.list(True))
        self.update()
        if event:
            event.Skip()

    def toogle_list(self, event):
        self.panel.DestroyChildren()
        if self.toogle_list_btn.IsToggled():
            self.panel.wrap_sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.panel.wrap_sizer = wx.WrapSizer()
        self.filter(None)

def main():
    app = DockerUI(redirect=False)
    scheduler = WxScheduler(wx)
    
    def on_next(containers):
        app.panel.DestroyChildren()

        for c in containers:
            static = Container(app.panel, app, c)
            app.panel.wrap_sizer.Add(static, 0, wx.ALL, border=5)

        app.update()     

    app.containers.subscribe(on_next, on_error=print, scheduler=scheduler)
    app.filter(None)

    app.frame.Bind(wx.EVT_CLOSE, lambda e: (scheduler.cancel_all(), e.Skip()))
    #scheduler.schedule_periodic(10, app.filter)

    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()