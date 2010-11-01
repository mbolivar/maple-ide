from __future__ import print_function

import wx

import settings
from settings import preferences

def get_instance():
    """Return the singleton instance."""
    global __instance
    if not __instance:
        __instance = PreferencesFrame()
    return __instance

__instance = None

class PreferencesFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Preferences")

        self.pnl = wx.Panel(self)

        self.mgr = wx.aui.AuiManager()
        self.mgr.SetManagedWindow(self.pnl)

        self.Centre()

        # a notebook/tabbed pane stores the different categories of
        # preference.  CLIP_CHILDREN apparently reduces flicker?
        self.nb = wx.Notebook(self.pnl, wx.ID_ANY, style=wx.CLIP_CHILDREN)
        self._layout_nb()

        # save button
        # button_pnl = wx.Panel(self)
        # save_btn = wx.Button(button_pnl, wx.ID_SAVE)
        # # bsizer = wx.BoxSizer(wx.HORIZONTAL)
        # # bsizer.AddStretchSpacer()
        # # bsizer.Add(save_btn)
        # self.Bind(wx.EVT_BUTTON, self.OnSave, save_btn)

        self.mgr.AddPane(self.nb,
                         wx.aui.AuiPaneInfo().CenterPane().Name("nb"))
        # self.mgr.AddPane(button_pnl,
        #                  wx.aui.AuiPaneInfo().
        #                  Bottom().
        #                  Floatable(False).
        #                  MinSize(bsizer.GetMinSize()).
        #                  BestSize(bsizer.GetMinSize()).
        #                  CloseButton(False).
        #                  Name("but"))



        self.mgr.Update()

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
            if idx is None:
                self.nb.AddPage(wx.Panel(self.nb), group)
                idx = get_page_idx(group) # this is stupid
                sizers[idx]  = wx.BoxSizer(wx.VERTICAL)
            page = self.nb.GetPage(idx)
            sizer = sizers[idx]

            tt = wx.ToolTip(cfg.help)
            ptype = cfg.type
            if ptype == 'path':
                desc = wx.StaticText(page, wx.ID_ANY, cfg.desc + u':',
                                     style=wx.ALIGN_LEFT)
                desc.SetToolTip(tt)
                tc = wx.TextCtrl(page, wx.ID_ANY,
                                 preferences.preference(pref))

                self.pref_controls[pref] = tc

                sizer.AddSpacer(10)
                sizer.Add(desc, border=10, flag=wx.ALIGN_LEFT | wx.LEFT)
                sizer.Add(tc, border=40, flag=wx.EXPAND | wx.LEFT)
            elif ptype == 'bool':
                cb = wx.CheckBox(page, wx.ID_ANY, cfg.desc)
                cb.SetValue(preferences.preference(pref))
                cb.SetToolTip(tt)

                self.pref_controls[pref] = cb

                sizer.AddSpacer(10)
                sizer.Add(cb, border=10, flag=wx.ALIGN_LEFT | wx.LEFT)
            elif ptype == 'int':
                child_sizer = wx.BoxSizer(wx.HORIZONTAL)
                desc = wx.StaticText(page, wx.ID_ANY, cfg.desc,
                                     style=wx.ALIGN_LEFT)
                desc.SetToolTip(tt)
                tc = wx.TextCtrl(page, wx.ID_ANY,
                                 unicode(preferences.preference(pref)))

                self.pref_controls[pref] = tc

                child_sizer.Add(desc, flag=wx.EXPAND)
                child_sizer.AddSpacer(10)
                child_sizer.Add(tc)
                sizer.AddSpacer(10)
                sizer.Add(child_sizer, border=10, flag=wx.LEFT)

        for i in range(self.nb.GetPageCount()):
            page = self.nb.GetPage(i)
            sizer = sizers[i]
            page.SetSizer(sizer)


    def OnSave(self, evt):
        print("you clicked save.")
