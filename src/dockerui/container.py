import wx

class Container(wx.Panel):
    def __init__(self, parent, app, container):
        self.container = container
        self.parent = parent
        self.app = app
        super(Container, self).__init__(parent)

        if self.is_running():
            self.SetBackgroundColour(wx.Colour(120,200,120))
        elif self.is_exited():
            self.SetBackgroundColour(wx.Colour(120,120,120))
        else:
            self.SetBackgroundColour(wx.Colour(200,120,120))

        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)

        _name = wx.StaticText(self)
        _name.SetFont(wx.Font(wx.FontInfo(14).Bold()))
        _name.SetLabel(container.name)
        _image = wx.StaticText(self)
        _image.SetFont(wx.Font(wx.FontInfo(9).Italic()))
        _image.SetLabel(container.image.tags[0])
        _status = wx.StaticText(self)
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
        
        self.parent.Bind(wx.EVT_BUTTON, self.start, _start)
        self.parent.Bind(wx.EVT_BUTTON, self.stop, _stop)
        self.parent.Bind(wx.EVT_BUTTON, self.remove, _remove)
        self.parent.Bind(wx.EVT_BUTTON, self.shell, _shell)
        self.parent.Bind(wx.EVT_BUTTON, self.logs, _logs)
        
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
        self.app.filter(None)
        event.Skip();

    def stop(self, event):
        self.container.stop()
        self.app.filter(None)
        event.Skip();

    def remove(self, event):
        dlg = wx.MessageDialog(None, "Do you want to forcet remove the container",'Remove Container', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.container.stop()
            self.container.remove()
            self.app.filter(None)
        event.Skip();

    def shell(self, event):
        #self.container.stop()
        self.app.filter(None)
        event.Skip();

    def logs(self, event):
        #self.container.stop()
        self.app.filter(None)
        event.Skip();