from __future__ import print_function

from pprint import pprint

import wx

import settings
import wx_util
from settings import preferences

def get_instance():
    """Return the only instance, creating one if necessary."""
    global _instance
    if _instance is None:
        _instance = PreferencesFrame()
    return _instance

def _instance_closed():
    global _instance
    _instance = None

# not a singleton, but there's at most one.
_instance = None

_PAGE_MIN_SIZE = (600,200)

class PreferencesFrame(wx.Frame):
    """Don't instantiate this yourself; use get_instance() instead."""

    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Preferences")

        save_btn = wx.Button(self, id=wx.ID_SAVE)
        self.Bind(wx.EVT_BUTTON, self.OnSave, save_btn)

        cancel_btn = wx.Button(self, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, cancel_btn)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.nb = wx.Notebook(self, wx.ID_ANY)
        self._layout_nb()
        sizer.Add(self.nb, border=20, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)

        save_sizer = wx.BoxSizer(wx.HORIZONTAL)
        save_sizer.AddStretchSpacer()
        save_sizer.Add(cancel_btn, border=5, flag=wx.ALL)
        save_sizer.Add(save_btn, border=5, flag=wx.ALL)
        sizer.Add(save_sizer, flag=wx.ALIGN_RIGHT)

        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        self.Centre()

    def _layout_nb(self):

        def get_page_idx(group):
            for i in range(self.nb.GetPageCount()):
                if self.nb.GetPageText(i) == group:
                    return i
            return None

        sizers = {}
        self.pref_controls = {}

        # TODO better layout control (cheap start: make PREF_CONFIG ordered)
        config = sorted(preferences.PREF_CONFIG.iteritems(),
                        key=lambda pref_cfg: pref_cfg[1].group + pref_cfg[0])
        for pref, cfg in config:
            group = cfg.group
            idx = get_page_idx(group)
            value = preferences.preference(pref)
            if idx is None:
                self.nb.AddPage(wx.Panel(self.nb), group)
                idx = get_page_idx(group) # this is stupid
                sizers[idx]  = wx.BoxSizer(wx.VERTICAL)
            page = self.nb.GetPage(idx)
            sizer = sizers[idx]

            tt = wx.ToolTip(cfg.help)
            ptype = cfg.type
            if ptype == 'path' or ptype == 'dir':
                desc = wx.StaticText(page, wx.ID_ANY, cfg.desc + u':',
                                     style=wx.ALIGN_LEFT)
                desc.SetToolTip(tt)
                if ptype == 'path':
                    p = wx.FilePickerCtrl(page, wx.ID_ANY, path=value)
                else:
                    p = wx.DirPickerCtrl(page, wx.ID_ANY, path=value)

                self.pref_controls[pref] = p

                sizer.AddSpacer(10)
                sizer.Add(desc, border=10, flag=wx.ALIGN_LEFT | wx.LEFT)
                sizer.Add(p, border=40, flag=wx.LEFT | wx.EXPAND)
            elif ptype == 'bool':
                cb = wx.CheckBox(page, wx.ID_ANY, cfg.desc)
                cb.SetValue(value)
                cb.SetToolTip(tt)

                self.pref_controls[pref] = cb

                sizer.AddSpacer(10)
                sizer.Add(cb, border=10, flag=wx.ALIGN_LEFT | wx.LEFT)
            elif ptype == 'int':
                child_sizer = wx.BoxSizer(wx.HORIZONTAL)
                desc = wx.StaticText(page, wx.ID_ANY, cfg.desc,
                                     style=wx.ALIGN_LEFT)
                desc.SetToolTip(tt)
                tc = wx.TextCtrl(page, wx.ID_ANY, unicode(value))

                self.pref_controls[pref] = tc

                child_sizer.Add(desc, flag=wx.EXPAND)
                child_sizer.AddSpacer(10)
                child_sizer.Add(tc)
                sizer.AddSpacer(10)
                sizer.Add(child_sizer, border=10, flag=wx.LEFT)
            elif ptype == 'options':
                values = cfg.data['values']

                child_sizer = wx.BoxSizer(wx.HORIZONTAL)
                desc = wx.StaticText(page, wx.ID_ANY, cfg.desc,
                                     style=wx.ALIGN_LEFT)
                desc.SetToolTip(tt)
                c = wx.Choice(page, wx.ID_ANY, choices=values)
                c.SetSelection(values.index(value))

                self.pref_controls[pref] = c

                child_sizer.Add(desc)
                child_sizer.AddSpacer(10)
                child_sizer.Add(c)
                sizer.Add(child_sizer, border=10, flag=wx.LEFT)
            else:
                die(u'Unknown preference type: {0}'.format(ptype))

        for i in range(self.nb.GetPageCount()):
            page = self.nb.GetPage(i)
            sizer = sizers[i]
            sizer.SetMinSize(_PAGE_MIN_SIZE)
            page.SetSizer(sizer)


    def OnSave(self, evt):
        controller_vals = {}
        for pref, control in self.pref_controls.iteritems():
            cfg = preferences.PREF_CONFIG[pref]
            ptype = cfg.type
            if ptype == 'path' or ptype == 'dir':
                controller_vals[pref] = control.GetPath()
            elif ptype == 'bool':
                controller_vals[pref] = control.IsChecked()
            elif ptype == 'int':
                err = u'Cannot save preference {0}. '.format(cfg.desc)
                err += u'Preference must be a number greater than zero'

                try:
                    val = int(control.GetValue())
                except:
                    wx_util.error_popup(err)
                    return

                if val <= 0:
                    wx_util.error_popup(err)
                    return

                controller_vals[pref] = val
            elif ptype == 'options':
                values = cfg.data['values']
                controller_vals[pref] = values[control.GetSelection()]
            else:
                die('unknown ptype {0}'.format(ptype))
        preferences.set_and_save(controller_vals)
        _instance_closed()
        self.Close()

    def OnCancel(self, evt):
        self.Close()

    def OnClose(self, evt):
        _instance_closed()
        evt.Skip()
