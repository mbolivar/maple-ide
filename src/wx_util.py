"""Utility wx functions.
"""

import wx

def not_implemented_popup():
    popup = wx.MessageDialog(None, "Sorry!", "Not implemented yet", wx.OK)
    popup.ShowModal()
    popup.Destroy()

def warning_popup(message, details):
    popup = wx.MessageDialog(None, "Warning: " + message, details,
                             wx.ICON_EXCLAMATION)
    popup.ShowModal()
    popup.Destroy()

def error_popup(message, details):
    popup = wx.MessageDialog(None, "Error: " + msg, details, wx.ICON_ERROR)
    popup.ShowModal()
    popup.Destroy()
