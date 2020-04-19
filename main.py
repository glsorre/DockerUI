import docker
import rx

from rx import operators as ops
from rx.subject import Subject
from rx.scheduler.mainloop import WxScheduler

import wx
import wx.lib.scrolledpanel as scrolled
from wx.lib.stattext import GenStaticText as StaticText

client = docker.from_env()

class Event():
    def __init__(self):
        print("generating fake event")
    def Skip(self):
        print("force update")

FAKE_EVENT = Event()

class ContainerPanel(wx.Panel):
    def __init__(self, parent, container):
        self.container = container
        self.parent = parent
        super(ContainerPanel, self).__init__(parent)

        if self.is_running():
            self.SetBackgroundColour(wx.Colour(120,200,120))
        elif self.is_exited():
            self.SetBackgroundColour(wx.Colour(120,120,120))
        else:
            self.SetBackgroundColour(wx.Colour(200,120,120))

        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)

        _name = StaticText(self)
        _name.SetFont(wx.Font(wx.FontInfo(14).Bold()))
        _name.SetLabel(container.name)
        _image = StaticText(self)
        _image.SetFont(wx.Font(wx.FontInfo(9).Italic()))
        _image.SetLabel(container.image.tags[0])
        _status = StaticText(self)
        _status.SetFont(wx.Font(wx.FontInfo(9)))
        _status.SetLabel(container.status.upper())
        
        _start = wx.Button(self, label='Start')
        _stop = wx.Button(self, label='Stop')
        _remove = wx.Button(self, label='Remove')
        _shell = wx.Button(self, label='Shell')
        _logs = wx.Button(self, label='Logs')

        _start.Hide()
        _stop.Hide()
        _remove.Hide()
        _shell.Hide()
        _logs.Hide()
        
        self.parent.parent.Bind(wx.EVT_BUTTON, self.start, _start)
        self.parent.parent.Bind(wx.EVT_BUTTON, self.stop, _stop)
        self.parent.parent.Bind(wx.EVT_BUTTON, self.remove, _remove)
        self.parent.parent.Bind(wx.EVT_BUTTON, self.shell, _shell)
        self.parent.parent.Bind(wx.EVT_BUTTON, self.logs, _logs)
        
        container_toolbar = wx.BoxSizer(wx.HORIZONTAL)
        if self.is_running():
            _stop.Show()
            _remove.Show()
            _shell.Show()
            _logs.Show()
            container_toolbar.Add(_stop, 0, wx.EXPAND | wx.ALL, border=4)
            container_toolbar.Add(_shell, 0, wx.EXPAND | wx.ALL, border=4)
            container_toolbar.Add(_logs, 0, wx.EXPAND | wx.ALL, border=4)
            container_toolbar.Add(_remove, 0, wx.EXPAND | wx.ALL, border=4)
        else:
            _start.Show()
            _remove.Show()
            container_toolbar.Add(_start, 0, wx.EXPAND | wx.ALL, border=4)
            container_toolbar.Add(_remove, 0, wx.EXPAND | wx.ALL, border=4)


        self.panel_sizer.Add(_name, 0, wx.EXPAND | wx.ALL, border=4)
        self.panel_sizer.Add(_image, 0, wx.EXPAND | wx.ALL, border=4)
        self.panel_sizer.Add(_status, 0, wx.EXPAND | wx.ALL, border=4)
        self.panel_sizer.Add(container_toolbar, 0, wx.EXPAND | wx.ALL, border=4)

        self.SetSizer(self.panel_sizer)

    def is_running(self):
        return self.container.status == 'running'

    def is_exited(self):
        return self.container.status == 'exited'

    def start(self, event):
        self.container.start()
        self.parent.parent.UpdateContainers(FAKE_EVENT)
        event.Skip();

    def stop(self, event):
        self.container.stop()
        self.parent.parent.UpdateContainers(FAKE_EVENT)
        event.Skip();

    def remove(self, event):
        dlg = wx.MessageDialog(None, "Do you want to forcet remove the container",'Remove Container', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.container.stop()
            self.container.remove()
            self.parent.parent.UpdateContainers(FAKE_EVENT)
        event.Skip();

    def shell(self, event):
        #self.container.stop()
        self.parent.parent.UpdateContainers(FAKE_EVENT)
        event.Skip();

    def logs(self, event):
        #self.container.stop()
        self.parent.parent.UpdateContainers(FAKE_EVENT)
        event.Skip();

class Panel(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, style=wx.VSCROLL)
        self.parent = parent
        self.grid_sizer = wx.WrapSizer()
        self.SetupScrolling()
        self.SetSizer(self.grid_sizer)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        size = self.parent.GetSize()
        vsize = self.parent.GetVirtualSize()
        self.SetVirtualSize((size[0], vsize[1]))
        self.SetupScrolling()
        self.SetSizer(self.grid_sizer)
        event.Skip()

class Frame(wx.Frame):
    def __init__(self):
        super(Frame, self).__init__(None)
        self.SetTitle("DockerUI")
        self.SetSize(600, 600)

        self.containers = Subject()

        self.panel = Panel(self)

        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        text_ctrl = wx.TextCtrl(self)
        text_ctrl.SetHint("Search...")
        self.Bind(wx.EVT_TEXT, self.FilterContainers, text_ctrl)

        update_btn = wx.Button(self, wx.ID_REFRESH)
        update_btn.Bind(wx.EVT_BUTTON, self.UpdateContainers)

        ctrl_sizer.Add(text_ctrl, wx.ALL, wx.ALL, border=10)
        ctrl_sizer.Add(update_btn, 1, wx.ALL, border=10)  

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)        
        self.main_sizer.Add(ctrl_sizer, 0, wx.ALL, border=10)
        self.main_sizer.Add(self.panel, -1, wx.EXPAND | wx.ALL, border=10)

        self.SetSizer(self.main_sizer)

    def UpdateContainers(self, event):
        self.containers.on_next(client.containers.list(True))
        if event:
            event.Skip()

    def FilterContainers(self, event):
        event.Skip()
        if event.GetEventObject().GetValue():
            result = list(filter(lambda c: c.name.startswith(event.GetEventObject().GetValue()), client.containers.list(True)))
            self.containers.on_next(result)
        else:
            print("ci siamo")
            self.containers.on_next(client.containers.list(True))

def main():
    app = wx.App(redirect=False)
    scheduler = WxScheduler(wx)

    app.TopWindow = frame = Frame()
    frame.Show()
    
    def on_next(containers):
        frame.panel.DestroyChildren()

        for c in containers:
            static = ContainerPanel(frame.panel, c)
            frame.panel.grid_sizer.Add(static, 0, wx.ALL, border=10)

        frame.panel.SetSizer(frame.panel.grid_sizer)
        frame.panel.SetupScrolling()
        frame.SetSizer(frame.main_sizer)

    frame.containers.subscribe(on_next, on_error=print, scheduler=scheduler)
    frame.UpdateContainers(FAKE_EVENT)

    frame.Bind(wx.EVT_CLOSE, lambda e: (scheduler.cancel_all(), e.Skip()))
    scheduler.schedule_periodic(10, frame.UpdateContainers)
    app.MainLoop()

if __name__ == '__main__':
    main()