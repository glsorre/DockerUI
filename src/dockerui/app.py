from src.dockerui.container import Container

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
    def OnInit(self):
        self.res = wx.xrc.XmlResource.Get()
        self.res.LoadFile(RSRC_FILE)
        self.containers = Subject()
        self.render()
        self.toolbar()
        return True
    
    def render(self, is_list=False):
        self.frame = self.res.LoadFrame(None, RSRC_FRAMENAME)
        self.SetTopWindow(self.frame)
        self.window = wx.xrc.XRCCTRL(self.frame, "mainWindow")
        self.panel = wx.xrc.XRCCTRL(self.frame, "containersPanel")
        self.panel.grid_sizer = wx.WrapSizer()
        self.window.SetScrollRate(1,1)
        self.frame.Bind(wx.EVT_SIZE, self.on_size)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE))
        self.frame.Show()

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
        self.panel.SetSizer(self.panel.grid_sizer)
        self.frame.SendSizeEvent()

    def on_size(self, event):
        size = self.frame.GetSize()
        vsize = self.frame.GetVirtualSize()
        self.panel.SetSizer(self.panel.grid_sizer)
        self.panel.SetVirtualSize((size[0], vsize[1]))
        self.window.SetVirtualSize((size[0], vsize[1]))
        self.panel.Layout()
        self.window.Layout()
        event.Skip()

    def filter(self, event):
        if event:
            event.Skip()

        text = self.text_ctrl.GetValue()
        if text:
            result = list(filter(lambda c: c.name.startswith(text), client.containers.list(True)))
            self.containers.on_next(result)
        else:
            self.containers.on_next(client.containers.list(True))

    def toogle_list(self, event):
        event.Skip()
        if self.toogle_list_btn.IsToggled():
            self.panel.DestroyChildren()
            self.panel.grid_sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.panel.DestroyChildren()
            self.panel.grid_sizer = wx.WrapSizer()
        self.filter(None)

def main():
    app = DockerUI()
    scheduler = WxScheduler(wx)
    
    def on_next(containers):
        app.panel.DestroyChildren()

        for c in containers:
            static = Container(app.panel, app, c)
            app.panel.grid_sizer.Add(static, 0, wx.ALL, border=10)

        app.update()     

    app.containers.subscribe(on_next, on_error=print, scheduler=scheduler)
    app.filter(None)

    app.frame.Bind(wx.EVT_CLOSE, lambda e: (scheduler.cancel_all(), e.Skip()))
    scheduler.schedule_periodic(10, app.filter)

    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()