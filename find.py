#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import wx
import wx.lib.mixins.listctrl  as  listmix
import logging
import os, fnmatch
import glob
import subprocess

logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('zim_searching')
#---------------------------------------------------------------------------


class TestListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class ZimSearch(wx.Frame, listmix.ColumnSorterMixin):
    def __init__(self, parent, id, title, notebook_name, root_path):
        wx.Frame.__init__(self, parent, id, title, size=(650, 400))

        self.log = logger
        self.rootPath = root_path
        self.notebookName = notebook_name 

        self.layout()

        #
        # Event
        #
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.list.Bind(wx.EVT_CHAR, self.OnListChar)
        self.input.Bind(wx.EVT_CHAR, self.OnInputChar)
        self.Bind(wx.EVT_BUTTON, self.OnSearch, id = self.btnSearch.GetId())
        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)

    def layout(self):
        panel = wx.Panel(self)
        tID = wx.NewId()

        sizer = wx.BoxSizer(wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)

        #
        # horizontal 1
        #
        vbox1_1 = wx.BoxSizer(wx.HORIZONTAL)
        self.input = wx.TextCtrl(panel, -1)
        vbox1_1.Add(self.input, 1, wx.EXPAND)

        tId = wx.NewId()
        self.btnSearch = wx.Button(panel, tId, label='Search')
        vbox1_1.Add(self.btnSearch, 0, wx.LEFT | wx.RIGHT, 5)

        hbox1.Add(vbox1_1, wx.EXPAND)

        #
        # horizontal 2
        #
        line = wx.StaticLine(panel)
        hbox2.Add(line, 1, wx.EXPAND)

        #
        # horizontal 3
        #
        self.list = TestListCtrl(panel, tID,
                                 style=wx.LC_REPORT
                                 | wx.BORDER_SUNKEN
                                 #| wx.BORDER_NONE
                                 #| wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 #| wx.LC_NO_HEADER
                                 | wx.LC_VRULES
                                 | wx.LC_HRULES)
                                 #| wx.LC_SINGLE_SEL
        hbox3.Add(self.list, 1, wx.EXPAND)
        self.PopulateList()


        #
        #
        #
        sizer.Add(hbox1, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.BOTTOM, 5)
        sizer.Add(hbox2, 0, wx.EXPAND | wx.BOTTOM, 5)
        sizer.Add(hbox3, 1, wx.EXPAND)

        # Now that the list exists we can init the other base class,
        # see wx/lib/mixins/listctrl.py
        listmix.ColumnSorterMixin.__init__(self, 2)
        #self.SortListItems(0, True)

        panel.SetSizer(sizer)
        self.CreateStatusBar()
        self.Centre()
        self.input.SetFocus()


    def Search(self, status, keyword = ''):
        def find_files(directory, pattern):
            for root, dirs, files in os.walk(directory):
                for basename in files:
                    if fnmatch.fnmatch(basename, pattern):
                        filename = os.path.join(root, basename)
                        yield filename
        self.log.debug('Start searching with value %s' % (keyword))
        items = []
        for file in find_files(self.rootPath, '*.txt'):
            count = 0
            if not os.path.isfile(file):
                continue
            if file.find(keyword) >= 0:
                count += 10
            for line in open(file):
                if line.find(keyword) >= 0:
                    count += 1
            if count > 0:
                items.append([file, count])
        sorted_items = sorted(items, key=lambda item: -item[1])
        for item in sorted_items:
            index = self.list.InsertStringItem(sys.maxint, item[0])
            self.list.SetStringItem(index, 1, str(item[1]))
        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, wx.LIST_AUTOSIZE)

    def OnSearch(self, event):
        self.Search(True, self.input.GetValue().encode("utf-8"))

    def OnClose(self, event):
        self.Search(False)
        self.Destroy()

    def PopulateList(self):
        # but since we want images on the column header we have to do it the hard way:
        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = 0
        info.m_text = "filename"
        self.list.InsertColumnInfo(0, info)

        info.m_format = 0
        info.m_text = "#"
        self.list.InsertColumnInfo(1, info)

    def OnInputChar(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.OnSearch(event)
            self.list.SetFocus()
            self.log.debug("OnInputChar Enter pressed")
        elif event.GetKeyCode() == wx.WXK_DOWN:
            self.log.debug("OnInputChar Down pressed")
        elif event.GetKeyCode() == wx.WXK_TAB:
            self.log.debug("OnInputChar Tab pressed")
        else:
            self.log.debug('OnInputChar: %d' % event.GetKeyCode())
        event.Skip()

    def OnListChar(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.log.debug("List Enter pressed")
            self.OpenZimFile()
        elif event.GetKeyCode() == wx.WXK_DOWN:
            self.log.debug("List Down pressed")
        elif event.GetKeyCode() == wx.WXK_UP:
            self.log.debug("List Up pressed")
        else:
            self.log.debug('OnListChar: %d' % event.GetKeyCode())
        event.Skip()

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    def OnDoubleClick(self, event):
        self.OpenZimFile()
        event.Skip()

    def OpenZimFile(self):
        next = self.list.GetNextItem(-1, state = wx.LIST_STATE_SELECTED)
        if next < 0:
            return
        filename = self.list.GetItem(next, 0).GetText();
        if len(filename) <= len(self.rootPath):
            return
        if not filename.endswith('.txt'):
            return
        filename = filename[len(self.rootPath):-4]
        filename = filename.replace(os.sep, ":")
        filename = filename.strip(':')
        self.log.debug("Final filename " + filename)
        subprocess.call(['zim', self.notebookName, filename])
        #zim dropbox "android:ep90"

#---------------------------------------------------------------------------


if __name__ == '__main__':
    if len(sys.argv) == 3:
        app = wx.App()
        root_path = os.path.realpath(sys.argv[2])
        notebook_name = sys.argv[1]
        frame = ZimSearch(None, -1, "zim searching", notebook_name, root_path)
        frame.Show()
        app.MainLoop()
    sys.exit(-1)
    #./main.py dropbox /home/doro/Dropbox/mynotes/
