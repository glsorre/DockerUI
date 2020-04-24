import sys
import time

import docker

from rx.scheduler.mainloop import WxScheduler

import wx
import wx.lib.inspection
import wx.xrc

from src.dockerui.utils import Container

RSRC_FILE = "src/dockerui/app.xrc"
RSRC_FRAMENAME = "mainFrame"

BORDER_MAIN = 5

client = docker.from_env()

class DockerUI(wx.App):
    view_list = False

    def OnInit(self):
        self.res = wx.xrc.XmlResource.Get()
        self.res.LoadFile(RSRC_FILE)
        self.render()
        self.toolbar()
        self.menu()
        self.frame.Show()
        self.frame.Layout()
        return True
    
    def render(self):
        self.frame = self.res.LoadFrame(None, RSRC_FRAMENAME)
        self.SetTopWindow(self.frame)
        self.notebook = wx.xrc.XRCCTRL(self.frame, "mainNotebook")
        self.window = wx.xrc.XRCCTRL(self.frame, "containersWindow")
        self.panel = wx.xrc.XRCCTRL(self.frame, "containersPanel")
        self.page = wx.xrc.XRCCTRL(self.frame, "containersPage")
        self.window.SetScrollRate(BORDER_MAIN,BORDER_MAIN)
        self.frame.SetSize(600,600)
        self.frame.Bind(wx.EVT_SIZE, self.on_size)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE))
        self.notebook.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE))
        self.panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

    def menu(self):
        menu_bar  = wx.MenuBar()
        help_menu = wx.Menu()

        help_menu.Append(wx.ID_ABOUT, "&About")
        menu_bar.Append(help_menu, "&Help")

        self.frame.SetMenuBar(menu_bar)
        #self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)

    def toolbar(self):
        self.toolbar = wx.ToolBar(self.frame)
        self.toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE))
        self.text_ctrl = wx.TextCtrl(self.toolbar)
        self.text_ctrl.SetHint("Search")  

        bmp = wx.ArtProvider.GetBitmap(wx.ART_UNDO)

        self.frame.SetToolBar(self.toolbar)

        self.toogle_list_btn = self.toolbar.AddCheckTool(wx.ID_ANY, 'Toogle list view', bmp)
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddControl(self.text_ctrl)
        self.refresh = self.toolbar.AddTool(wx.ID_ANY, 'Refresh', bmp)

        self.frame.Bind(wx.EVT_TEXT, self.refresh_action, self.text_ctrl)
        self.frame.Bind(wx.EVT_TOOL, self.refresh_action, self.refresh)
        self.frame.Bind(wx.EVT_TOOL, self.toogle_list_action, self.toogle_list_btn)

        self.toolbar.Realize()

    def refresh_containers(self, scheduler, state):
        print("refreshing containers")
        containers_list = self.get_containers_list()
        print(containers_list)

        self.panel.Hide()
        if state["is_list"]:
            new_sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            new_sizer = wx.WrapSizer()

        if self.panel.GetSizer().GetItemCount() > 0:
            self.panel.DestroyChildren()
            self.panel.GetSizer().Remove(0)

        for c in containers_list:
            static = Container(self.panel, self, state, c)
            state['containers'].append(c)
            new_sizer.Add(static, 0, wx.ALL|wx.EXPAND, border=BORDER_MAIN)
        
        self.panel.GetSizer().Add(new_sizer, 0, wx.ALL|wx.EXPAND)
        self.panel.Show()
        self.refresh_view()

    def refresh_view(self):
        print("resizing")
        page_size = self.page.GetMinSize()
        sizer_size = self.panel.GetSizer().CalcMin()
        container_bigger_size = self.panel.GetChildren()[self.get_bigger_container()].GetSize()
        self.panel.SetMinSize((container_bigger_size[0], sizer_size[1]))
        self.panel.SetMaxSize((page_size[0], (sys.maxsize * 2 + 1)))
        self.panel.GetSizer().Layout()
        self.panel.Layout()

    def on_size(self, event):
        self.refresh_view()
        event.Skip()

    def get_containers_list(self):
        print("getting containers list")
        text = self.text_ctrl.GetValue()
        result = client.containers.list(True, filters={"name":self.text_ctrl.GetValue()})
        return result

    def refresh_action(self, event):
        self.scheduler.schedule(self.refresh_containers, state)
        event.Skip()

    def toogle_list_action(self, event):
        print("toggling list view")
        state["is_list"] = self.toogle_list_btn.IsToggled()
        self.scheduler.schedule(self.refresh_containers, state)
        event.Skip()

    def get_bigger_container(self):
        bigger = 0
        bigger_size = 0

        for i, c in enumerate(self.panel.GetChildren()):
            if c.GetSize()[0] > bigger_size:
                bigger = i
                bigger_size = c.GetSize()[0] + BORDER_MAIN

        print(f"the bigger container is n {bigger}")
        return bigger

def main():
    app = DockerUI(redirect=False)
    app.scheduler = WxScheduler(wx)

    global state
    state = {
        "containers": [],
        "images": [],
        "is_list": False
    }

    app.frame.Bind(wx.EVT_CLOSE, lambda e: (app.scheduler.cancel_all(), e.Skip()))
    app.scheduler.schedule(app.refresh_containers, state)

    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()