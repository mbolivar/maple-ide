"""Utility wx functions.
"""

import wx

def not_implemented_popup():
    popup = wx.MessageDialog(None, "Sorry!", "Not implemented yet", wx.OK)
    popup.ShowModal()
    popup.Destroy()

def warning_popup(message, details):
    popup = wx.MessageDialog(None, details, message,
                             wx.ICON_EXCLAMATION)
    popup.ShowModal()
    popup.Destroy()

def error_popup(message, details):
    popup = wx.MessageDialog(None, details, message, wx.ICON_ERROR)
    popup.ShowModal()
    popup.Destroy()

def save_prompt_popup(caption, message):
    popup = wx.MessageDialog(None, message,
                             caption=caption,
                             style=wx.YES_NO|wx.CANCEL|wx.YES_DEFAULT)
    result = popup.ShowModal()
    popup.Destroy()
    return result
