import time
from datetime import datetime
import functions
import os
import wx
import wx.xrc
import wx.aui
import wx.grid
from schema import *
import sqlite3
import sqlalchemy
from data_extractor import data_info_dict as field_description_dict

_version = "2.0"
default_database_path = "C:\\Users\\Public\\Documents"  # default


class mainFrame(wx.Frame):
    """Frame that opens once the program"""

    def __init__(self, parent):
        # creates frame for initial seleciton menu. // could add size changer, version...
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"MIB database manager", pos=wx.DefaultPosition,
                          size=wx.Size(566, 331), style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE | wx.TAB_TRAVERSAL)

        # makes previous size the default
        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        # determines colour
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNHIGHLIGHT))

        # size of buttons
        gSizer2 = wx.GridSizer(1, 2, 0, 0)

        # panel, ID_ANY because id is irrelevant
        self.m_panel9 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer12 = wx.BoxSizer(wx.VERTICAL)

        # button objects with own variables. CREATION OF INITIAL BUTTONS with wx.Button
        self.m_button11 = wx.Button(self.m_panel9, wx.ID_ANY, u"Create\nnew\ndatabase",
                                    wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button11.SetFont(
            wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        # left button size
        bSizer12.Add(self.m_button11, 1, wx.ALL | wx.EXPAND, 5)

        #  calls to activate setsizer and layout using self.m_panel19
        self.m_panel9.SetSizer(bSizer12)
        self.m_panel9.Layout()
        bSizer12.Fit(self.m_panel9)
        gSizer2.Add(self.m_panel9, 1, wx.EXPAND | wx.ALL, 5)

        #  a panel is a window on which the controls are placed.
        self.m_panel10 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer121 = wx.BoxSizer(wx.VERTICAL)

        # database button
        self.openDatabase_button = wx.Button(self.m_panel10, wx.ID_ANY, u"Open\nExisting\ndatabase",
                                             wx.DefaultPosition, wx.DefaultSize, 0)
        self.openDatabase_button.SetFont(
            wx.Font(24, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        # right button size
        bSizer121.Add(self.openDatabase_button, 1, wx.ALL | wx.EXPAND, 5)

        # position location of button
        self.m_panel10.SetSizer(bSizer121)
        self.m_panel10.Layout()
        bSizer121.Fit(self.m_panel10)
        gSizer2.Add(self.m_panel10, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(gSizer2)
        self.Layout()

        # centres both buttons in panel
        self.Centre(wx.BOTH)

        #  Connect Events
        self.m_button11.Bind(wx.EVT_BUTTON, self.promptDatabaseLocation)
        self.openDatabase_button.Bind(wx.EVT_BUTTON, self.openExistingDatabse)

    def promptDatabaseLocation(self, event):
        print("Creating a new database")
        global create_database_dialog
        create_database_dialog = savingLocationDialog(self)
        create_database_dialog.Show()

    def createNewDatabase(self):
        #  create database file
        global engine

        #  createConnection(imported_database_path + "\\database.db")
        #  engine = sqlalchemy.create_engine
        #  ('sqlite:///' + imported_database_path.replace('\\', '/')
        #  + '/database.db', echo=False)
        createConnection(':memory:')

        # creates a database with specific pathway
        engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=False)
        Base.metadata.create_all(engine)

        # binds session to the created engine
        Session = sqlalchemy.orm.sessionmaker(bind=engine)
        global session
        session = Session()

        #  create text files
        functions.exportDatabase(engine, session, imported_database_path, True)
        self.Destroy()

        #  notify the user
        global notification_frame
        notification_frame = databaseSavedDialog(self)

        #  create workspace frame
        global workspace_frame
        workspace_frame = workspaceFrame(None)
        workspace_frame.Show()

    # func that creates existing database.
    def openExistingDatabse(self, event):
        print("open existing database")
        global import_database_dialog
        import_database_dialog = importDatabaseDialog(None)
        import_database_dialog.Show()


class workspaceFrame(wx.Frame):
    """window where virtually everything happens"""

    def __init__(self, parent):
        #  initialising variables
        global imported_database_path
        global saved_database_path
        saved_database_path = imported_database_path
        self.selected_row = None
        self.selected_column = None
        self.selected_grid = None
        self.selected_object_attributes = None
        self.selected_class_attributes = None
        self.enable_select = True

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"MIB database manager", pos=wx.DefaultPosition,
                          size=wx.Size(930, 607), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        #  Top menubar
        self.workspace_menubar = wx.MenuBar(0)
        self.file_menu = wx.Menu()
        self.importedLocation_menuItem = wx.MenuItem(self.file_menu, wx.ID_ANY, u"Open different database",
                                                     wx.EmptyString, wx.ITEM_NORMAL)
        self.file_menu.Append(self.importedLocation_menuItem)

        self.quit_menuItem = wx.MenuItem(self.file_menu, wx.ID_ANY, u"Quit", wx.EmptyString, wx.ITEM_NORMAL)
        self.file_menu.Append(self.quit_menuItem)

        self.workspace_menubar.Append(self.file_menu, u"File")

        self.save_menu = wx.Menu()

        self.save_menuItem = wx.MenuItem(self.save_menu, wx.ID_ANY, u"Save session" + u"\t" + u"CTRL+S", wx.EmptyString,
                                         wx.ITEM_NORMAL)
        self.save_menu.Append(self.save_menuItem)

        #  self.saveDatabase_menuItem = wx.MenuItem
        #  ( self.save_menu, wx.ID_ANY, u"Save database file",
        #  wx.EmptyString, wx.ITEM_NORMAL )
        #  self.save_menu.Append( self.saveDatabase_menuItem )

        self.savingLocation_menuItem = wx.MenuItem(self.save_menu, wx.ID_ANY, u"Change saving location", wx.EmptyString,
                                                   wx.ITEM_NORMAL)
        self.save_menu.Append(self.savingLocation_menuItem)

        self.workspace_menubar.Append(self.save_menu, u"Save")

        self.about_menu = wx.Menu()
        self.version_menuItem = wx.MenuItem(self.about_menu, wx.ID_ANY,
                                            u"Version", wx.EmptyString, wx.ITEM_NORMAL)
        self.about_menu.Append(self.version_menuItem)

        self.tableOrder_menuItem = wx.MenuItem(self.about_menu, wx.ID_ANY,
                                               u"Table input order",
                                               wx.EmptyString, wx.ITEM_NORMAL)
        self.about_menu.Append(self.tableOrder_menuItem)

        self.workspace_menubar.Append(self.about_menu, u"Help")

        self.actions_menu = wx.Menu()
        self.add_row_menuItem = wx.MenuItem(self.actions_menu, wx.ID_ANY,
                                            u"Add row" + u"\t" + u"CTRL+A",
                                            wx.EmptyString, wx.ITEM_NORMAL)
        self.actions_menu.Append(self.add_row_menuItem)

        self.edit_row_menuItem = wx.MenuItem(self.actions_menu, wx.ID_ANY,
                                             u"Edit row" + u"\t" + u"CTRL+E",
                                             wx.EmptyString, wx.ITEM_NORMAL)
        self.actions_menu.Append(self.edit_row_menuItem)

        self.delete_row_menuItem = wx.MenuItem(self.actions_menu, wx.ID_ANY,
                                               u"Delete Row" + u"\t" + u"CTRL+D",
                                               wx.EmptyString, wx.ITEM_NORMAL)
        self.actions_menu.Append(self.delete_row_menuItem)

        self.workspace_menubar.Append(self.actions_menu, u"Actions")

        self.SetMenuBar(self.workspace_menubar)

        #  Rest of the window
        principal_fgSizer = wx.FlexGridSizer(1, 2, 0, 0)
        principal_fgSizer.AddGrowableCol(0)
        principal_fgSizer.AddGrowableRow(0)
        principal_fgSizer.SetFlexibleDirection(wx.BOTH)
        principal_fgSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.workspace_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.workspace_panel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))

        workspace_Sizer = wx.BoxSizer(wx.VERTICAL)

        #  Show tables
        self.table_tab_container = wx.aui.AuiNotebook(self.workspace_panel, wx.ID_ANY, wx.DefaultPosition,
                                                      wx.DefaultSize,
                                                      wx.aui.AUI_NB_TAB_MOVE | wx.aui.AUI_NB_TOP
                                                      | wx.aui.AUI_NB_WINDOWLIST_BUTTON | wx.aui.AUI_NB_SCROLL_BUTTONS)
        self.panel_tab = {}
        self.table_bSizer = {}
        self.table_grid = {}
        self.max_width_dict = {}
        # dictionary associating the event id of each table with its corresponding class
        self.tableTab_event_Id_dict = {}

        table_counter = 0
        for table in sorted(tablename_list):
            if table not in not_supported_tables:
                self.class_type = tablename_dict[table]
                column_names = functions.getColumnNames(self.class_type)[0]
                table_data = functions.getRowDataFromDB(self.class_type, session)
                self.max_width_dict.update({table: functions.getColumnWidth(table_data, self.class_type)})
                rows = len(table_data)
                columns = len(column_names)

                self.panel_tab.update({table: wx.Panel(self.table_tab_container, wx.ID_ANY, wx.DefaultPosition,
                                                       wx.DefaultSize, wx.TAB_TRAVERSAL)})
                self.panel_tab[table].Name = table + '_panel'
                self.table_tab_container.AddPage(self.panel_tab[table], table, False, wx.NullBitmap)

                self.table_bSizer.update({table: wx.BoxSizer(wx.VERTICAL)})

                self.table_grid.update(
                    {table: wx.grid.Grid(self.panel_tab[table], wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)})

                #  Grid
                self.table_grid[table].CreateGrid(rows, columns)
                self.table_grid[table].EnableEditing(False)
                self.table_grid[table].EnableGridLines(True)
                self.table_grid[table].EnableDragGridSize(False)
                self.table_grid[table].SetMargins(0, 0)

                #  Columns
                self.table_grid[table].AutoSizeColumns()
                self.table_grid[table].EnableDragColMove(False)
                self.table_grid[table].EnableDragColSize(True)
                self.table_grid[table].SetColLabelSize(30)
                self.table_grid[table].SetColLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
                for j in range(columns):
                    self.table_grid[table].SetColLabelValue(j, column_names[j])
                    self.table_grid[table].SetColSize(j, 120)

                #  Rows
                self.table_grid[table].AutoSizeRows()
                self.table_grid[table].EnableDragRowSize(True)
                self.table_grid[table].SetRowLabelSize(40)
                self.table_grid[table].SetRowLabelAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

                #  Label Appearance
                self.table_grid[table].SetLabelBackgroundColour(wx.Colour(245, 231, 253))

                #  Cell Defaults
                self.table_grid[table].SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
                self.table_bSizer[table].Add(self.table_grid[table], 1, wx.ALL | wx.EXPAND, 5)

                #  fill the table
                for i in range(rows):
                    for j in range(columns):
                        #  print("loading cell %d\n" % i*j)
                        self.table_grid[table].SetCellValue(i, j, table_data[i][j])
                        if i % 2 == 0:
                            self.table_grid[table].SetCellBackgroundColour(i, j, wx.Colour(207, 242, 254))
                        else:
                            self.table_grid[table].SetCellBackgroundColour(i, j, wx.Colour(140, 235, 253))

                self.panel_tab[table].SetSizer(self.table_bSizer[table])
                self.panel_tab[table].Layout()
                self.table_bSizer[table].Fit(self.panel_tab[table])

                #  Connect Events
                self.table_grid[table].Bind(wx.grid.EVT_GRID_SELECT_CELL, self.selectedCell)
                self.tableTab_event_Id_dict.update({self.table_grid[table].GetId(): table})
                self.tableTab_event_Id_dict.update({table_counter: table})

                #  other
                if table_counter == 0:
                    self.tab_class_type = tablename_dict[table]
                table_counter += 1

        workspace_Sizer.Add(self.table_tab_container, 1, wx.EXPAND | wx.ALL, 5)

        self.workspace_panel.SetSizer(workspace_Sizer)
        self.workspace_panel.Layout()
        workspace_Sizer.Fit(self.workspace_panel)
        principal_fgSizer.Add(self.workspace_panel, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(principal_fgSizer)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        self.table_tab_container.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.tabEntered)
        self.Bind(wx.EVT_MENU, self.Quit, id=self.quit_menuItem.GetId())
        self.Bind(wx.EVT_CLOSE, self.Quit)
        self.Bind(wx.EVT_MENU, self.openDifferentDatabase, id=self.importedLocation_menuItem.GetId())
        self.Bind(wx.EVT_MENU, self.saveSession, id=self.save_menuItem.GetId())

        #  self.Bind( wx.EVT_MENU, self.saveDatabase, id = self.saveDatabase_menuItem.GetId() )
        self.Bind(wx.EVT_MENU, self.changeSavingLocation, id=self.savingLocation_menuItem.GetId())
        self.Bind(wx.EVT_MENU, self.displayVersion, id=self.version_menuItem.GetId())
        self.Bind(wx.EVT_MENU, self.tableOrder, id=self.tableOrder_menuItem.GetId())
        self.Bind(wx.EVT_MENU, self.addRow, id=self.add_row_menuItem.GetId())
        self.Bind(wx.EVT_MENU, self.editRow, id=self.edit_row_menuItem.GetId())
        self.Bind(wx.EVT_MENU, self.deleteRow, id=self.delete_row_menuItem.GetId())

    #  Virtual event handlers
    def selectedCell(self, event):
        if self.enable_select == True:
            """Sets the object's attributes of the selected row"""
            self.selected_row = event.GetRow()
            self.selected_column = event.GetCol()
            self.selected_grid = event.GetEventObject()
            self.selected_object_attributes = []
            self.selected_class_attributes = functions.getColumnNames(self.tab_class_type)[0]
            for j in range(len(self.selected_class_attributes)):
                self.selected_object_attributes.append(self.selected_grid.GetCellValue(self.selected_row, j))
            print(self.selected_object_attributes)
        else:
            pass

    def addRow(self, event):
        global add_frame
        add_frame = addFrame(self, mode='add')
        add_frame.Show()

    def editRow(self, event):
        global edit_row_frame
        edit_row_frame = addFrame(self, mode='edit', object_attributes=self.selected_object_attributes)
        edit_row_frame.Show()

    def deleteRow(self, event):
        global delete_row_dialog
        delete_row_dialog = deleteRowDialog(self)
        delete_row_dialog.Show()

    def displayVersion(self, event):
        """Displays informatin about the program"""
        self.version_dialog = infoDialog(self, "Version", "Version: %s\n05/08/2020" % _version)
        self.version_dialog.Show()

    def tableOrder(self, event):
        """Displays information about the order in which tables should be updated"""
        title = "Relative input order"
        text = "The suggested relative order in which the tables should be entered is as follows: "
        i = 1
        for table in suggested_input_order:
            if table not in not_supported_tables:
                text += "\n\t%s. %s" % (str(i), table)
                i += 1

        self.order_dialog = infoDialog(self, title, text)
        self.order_dialog.Show()

    def tabEntered(self, event):
        """Detects when a tab is entered and sets sel.tab_class_type"""
        selected_table = self.tableTab_event_Id_dict[event.Selection]
        #  print("%s tab entered" % selected_table)
        self.tab_class_type = tablename_dict[selected_table]

    def Quit(self, event):
        self.Destroy()
        session.close()
        conn.close()

    def saveDatabase(self, event):
        """Saves database as database file"""
        #  functions.exportDatabaseAsDB(engine, session, saved_database_path)
        pass

    def openDifferentDatabase(self, event):
        self.Destroy()
        global open_different_database_dialog
        open_different_database_dialog = importDatabaseDialog(None)
        open_different_database_dialog.Show()

    def saveSession(self, event):
        """Saves session onto text files. This function is called automatically
		each time a row is added."""
        saving_path = functions.exportDatabase(engine, session, saved_database_path, False)
        global database_saved_dialog
        if event != None:
            database_saved_dialog = databaseSavedDialog(self)
            database_saved_dialog.Show()

    def changeSavingLocation(self, event):
        """Prompts the user to enter a different saving location"""
        global change_saving_location_dialog
        change_saving_location_dialog = savingLocationDialog(self)
        change_saving_location_dialog.Show()

    def updateTable(self, table):
        """
        Updates one table in the worspace frame.
		input: table class as string
		"""

        # print("Updating %s_table ..." % table)
        rows = self.table_grid[table].GetNumberRows()
        col_sizes = self.table_grid[table].GetColSizes()
        if rows > 0:
            self.table_grid[table].DeleteRows(0, rows)

        self.class_type = tablename_dict[table]
        column_names = functions.getColumnNames(self.class_type)[0]
        table_data = functions.getRowDataFromDB(self.class_type, session)
        rows = len(table_data)
        columns = len(column_names)

        #  Grid
        self.table_grid[table].AppendRows(rows)

        #  Columns
        self.table_grid[table].AutoSizeColumns()
        self.table_grid[table].EnableDragColMove(False)
        self.table_grid[table].EnableDragColSize(True)
        self.table_grid[table].SetColLabelSize(30)
        self.table_grid[table].SetColSizes(col_sizes)

        #  Rows
        self.table_grid[table].AutoSizeRows()
        self.table_grid[table].EnableDragRowSize(True)

        #  Cell Defaults
        self.table_grid[table].SetDefaultCellAlignment(wx.ALIGN_LEFT, wx.ALIGN_CENTRE)

        #  fill the table
        for i in range(rows):
            for j in range(columns):

                #  print("loading cell %d\n" % i*j)
                self.table_grid[table].SetCellValue(i, j, table_data[i][j])
                if i % 2 == 0:
                    self.table_grid[table].SetCellBackgroundColour(i, j, wx.Colour(207, 242, 254))
                else:
                    self.table_grid[table].SetCellBackgroundColour(i, j, wx.Colour(140, 235, 253))

        #  Connect Events
        self.table_grid[table].Bind(wx.grid.EVT_GRID_SELECT_CELL, self.selectedCell)


class addFrame(wx.Frame):
    """
    Creates a new window that prompts the user to enter the different fields
	of a new row's table.
	Input:	optional keywod arguments: object_attributes (if mode is 'edit')
			mandatory keyword argumets: mode (add/ edit)
	"""

    def __init__(self, parent, **kwargs):
        self.class_type = parent.tab_class_type  # class type that will be used in this window
        self.kwargs = kwargs
        self.enable_description = False
        self.enable_toggle = False

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"MIB database manager", pos=wx.DefaultPosition,
                          size=wx.Size(
                              1000, 500), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        self.class_attributes, self.nullable_key_dict, self.foreign_keys_dict = functions.getColumnNames(
            self.class_type)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.add_frame_menubar1 = wx.MenuBar(0)
        self.view_menu = wx.Menu()
        self.m_menuItem2 = wx.MenuItem(self.view_menu, wx.ID_ANY, u"Datatype and maximum length", wx.EmptyString,
                                       wx.ITEM_CHECK)
        self.view_menu.Append(self.m_menuItem2)
        self.m_menuItem2.Check(True)

        self.m_menuItem21 = wx.MenuItem(self.view_menu, wx.ID_ANY, u"Enable/ Disable field override", wx.EmptyString,
                                        wx.ITEM_CHECK)
        self.view_menu.Append(self.m_menuItem21)
        self.m_menuItem21.Check(False)

        self.m_menuItem3 = wx.MenuItem(self.view_menu, wx.ID_ANY, u"Enable/ Disable field description", wx.EmptyString,
                                       wx.ITEM_CHECK)
        self.view_menu.Append(self.m_menuItem3)
        self.m_menuItem3.Check(False)

        self.add_frame_menubar1.Append(self.view_menu, u"View")

        self.SetMenuBar(self.add_frame_menubar1)

        principal_bSizer = wx.BoxSizer(wx.VERTICAL)

        self.header_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.header_panel.SetMinSize(wx.Size(-1, 50))

        header_gSizer = wx.GridSizer(1, 2, 5, 0)

        self.header_label = wx.StaticText(self.header_panel, wx.ID_ANY,
                                          u"Enter the following parameters. Once you are done, click the OK button on the right.",
                                          wx.DefaultPosition, wx.DefaultSize, 0)
        self.header_label.Wrap(-1)
        self.header_label.SetFont(
            wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        header_gSizer.Add(self.header_label, 1, wx.ALL | wx.EXPAND, 5)

        self.OK_button = wx.Button(self.header_panel, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        self.OK_button.SetFont(
            wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        header_gSizer.Add(self.OK_button, 1, wx.ALL | wx.EXPAND, 5)

        self.header_panel.SetSizer(header_gSizer)
        self.header_panel.Layout()
        header_gSizer.Fit(self.header_panel)
        principal_bSizer.Add(self.header_panel, 0, wx.ALL | wx.EXPAND, 5)

        self.input_data_scrolledWindow = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                                           wx.VSCROLL)
        self.input_data_scrolledWindow.SetScrollRate(5, 5)
        input_data_fgSizer = wx.FlexGridSizer(len(self.class_attributes), 4, 0, 5)
        input_data_fgSizer.SetFlexibleDirection(wx.BOTH)
        input_data_fgSizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        #  Fill the scrolledWindow where the values are to be prompted
        self.checkOverride_event_Id_dict = {}  # dictionary associating each check box with its attribute
        global override_attribute_dict

        # dictionary indicating whether to overrride a certain field
        override_attribute_dict = {}

        # list
        self.field_label = []
        self.value_textCtrl = []
        self.datatype_label = []
        self.checkOverride = []

        # dictionary associating the event Id of each mouse hover event with its corresponding attribute
        self.mouse_hover_Id_dict = {}
        i = 0
        for attribute in self.class_attributes:
            if self.nullable_key_dict[attribute] == False:
                self.field_label.append(
                    wx.StaticText(self.input_data_scrolledWindow, wx.ID_ANY, attribute, wx.DefaultPosition,
                                  wx.DefaultSize, 0))
                self.field_label[i].Wrap(-1)
                self.field_label[i].SetFont(
                    wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial Black"))
            else:
                self.field_label.append(
                    wx.StaticText(self.input_data_scrolledWindow, wx.ID_ANY, attribute, wx.DefaultPosition,
                                  wx.DefaultSize, 0))
                self.field_label[i].Wrap(-1)
                self.field_label[i].SetFont(
                    wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))
            input_data_fgSizer.Add(self.field_label[i], 1, wx.ALL | wx.EXPAND, 5)

            if self.foreign_keys_dict[attribute] == None:  # attribute is not a foreign key
                if kwargs['mode'] == 'edit':  # displays the current attributes of the object
                    if kwargs['object_attributes'][i] not in [None, '-']:
                        current_val = kwargs['object_attributes'][i]
                    else:
                        current_val = ''
                    self.value_textCtrl.append(
                        wx.TextCtrl(self.input_data_scrolledWindow, wx.ID_ANY, current_val, wx.DefaultPosition,
                                    wx.DefaultSize, 0))
                elif kwargs['mode'] == 'add':
                    self.value_textCtrl.append(
                        wx.TextCtrl(self.input_data_scrolledWindow, wx.ID_ANY, wx.EmptyString,
                                    wx.DefaultPosition, wx.DefaultSize, 0))

            else:  # attribute is a foreign key
                FK_comboBoxChoices = []
                for fk in self.foreign_keys_dict[attribute]:  # there may be multiple foreign tables
                    foreign_table = session.query(tablename_dict[fk['table']]).all()  # gets the foreign table
                    for foreign_row in foreign_table:
                        for key, value in foreign_row.__dict__.items():
                            if key == fk['field'] and value != None:
                                FK_comboBoxChoices.append(str(value))
                if kwargs['mode'] == 'edit':  # displays the current attributes of the object
                    if kwargs['object_attributes'][i] not in [None, '-']:
                        current_val = kwargs['object_attributes'][i]
                    else:
                        current_val = ''
                    self.value_textCtrl.append(
                        wx.ComboBox(self.input_data_scrolledWindow, wx.ID_ANY, current_val, wx.DefaultPosition,
                                    wx.DefaultSize, list(set(FK_comboBoxChoices)), 0))
                if kwargs['mode'] == 'add':
                    self.value_textCtrl.append(
                        wx.ComboBox(self.input_data_scrolledWindow, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition,
                                    wx.DefaultSize, list(set(FK_comboBoxChoices)), 0))
            input_data_fgSizer.Add(self.value_textCtrl[i], 1, wx.ALL | wx.EXPAND, 5)
            self.value_textCtrl[i].SetMinSize(wx.Size(400, -1))

            datatype, max_len = functions.getDatatypeAndLength(self.class_type, self.class_attributes[i])
            self.datatype_label_text = "Datatype: %s.\tMaximum number of characters: %s.  " % (datatype, str(max_len))

            #  print(self.datatype_label_text)
            #  unknown why this does not show the same text as on GUI panel
            self.datatype_label.append(
                wx.StaticText(self.input_data_scrolledWindow, wx.ID_ANY, self.datatype_label_text, wx.DefaultPosition,
                              wx.DefaultSize, 0))
            self.datatype_label[i].Wrap(-1)
            input_data_fgSizer.Add(self.datatype_label[i], 0, wx.ALL, 5)
            self.checkOverride.append(
                wx.CheckBox(self.input_data_scrolledWindow, wx.ID_ANY, u"Override", wx.DefaultPosition, wx.DefaultSize,
                            0))
            input_data_fgSizer.Add(self.checkOverride[i], 0, wx.ALL, 5)
            self.checkOverride_event_Id_dict.update({self.checkOverride[i]: self.class_attributes[i]})
            override_attribute_dict.update({self.class_attributes[i]: False})
            self.mouse_hover_Id_dict.update({self.field_label[i].GetId(): attribute})

            #  Connect events
            self.checkOverride[i].Bind(wx.EVT_CHECKBOX, self.overrideField)
            self.field_label[i].Bind(wx.EVT_ENTER_WINDOW, self.openInfo)
            self.field_label[i].Bind(wx.EVT_LEAVE_WINDOW, self.closeInfo)
            self.field_label[i].Bind(wx.EVT_LEFT_DCLICK, self.doubleClick)
            i += 1

        self.input_data_scrolledWindow.SetSizer(input_data_fgSizer)
        self.input_data_scrolledWindow.Layout()
        input_data_fgSizer.Fit(self.input_data_scrolledWindow)
        principal_bSizer.Add(self.input_data_scrolledWindow, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(principal_bSizer)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        self.Bind(wx.EVT_MENU, self.showDatatype, id=self.m_menuItem2.GetId())
        self.Bind(wx.EVT_MENU, self.showOverride, id=self.m_menuItem21.GetId())
        self.Bind(wx.EVT_MENU, self.enableDescription, id=self.m_menuItem3.GetId())
        self.OK_button.Bind(wx.EVT_BUTTON, self.onOKButton);
        self.mode = kwargs['mode']

        #  Hide items at first
        for item in self.checkOverride:
            item.Hide()

    def promptTable(self, *args):
        """OBSOLETE. Asks the user which table is to be handeled. First optional positional argument si the event"""
        try:  # deletes the dialog window
            self.update_dialog.Destroy()
            del self.update_dialog
            a = 0
        except AttributeError:  # dialog does not exist
            pass
        except NameError:
            pass

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        bSizer2 = wx.BoxSizer(wx.VERTICAL)
        self.m_scrolledWindow3 = wx.ScrolledWindow(
            self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL | wx.VSCROLL)
        self.m_scrolledWindow3.SetScrollRate(5, 5)
        bSizer3 = wx.BoxSizer(wx.VERTICAL)
        self.m_staticText79 = wx.StaticText(
            self.m_scrolledWindow3, wx.ID_ANY, u"Choose a table:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText79.Wrap(-1)
        self.m_staticText79.SetFont(
            wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial Black"))
        bSizer3.Add(self.m_staticText79, 0, wx.ALL, 5)

        self.m_button = []
        self.addTable_event_Id_dict = {}  # dictionary associating the event id of each button event with its corresponding class
        i = 0
        for item in sorted(tablename_list):
            self.m_button.append(
                wx.Button(self.m_scrolledWindow3, wx.ID_ANY, item, wx.DefaultPosition, wx.DefaultSize, 0))
            bSizer3.Add(self.m_button[i], 0, wx.ALL | wx.EXPAND, 5)
            self.addTable_event_Id_dict.update({self.m_button[i].GetId(): tablename_dict[item]})
            #  Connect Events
            self.m_button[i].Bind(wx.EVT_BUTTON, self.promptData)
            i += 1

        self.m_scrolledWindow3.SetSizer(bSizer3)
        self.m_scrolledWindow3.Layout()
        bSizer3.Fit(self.m_scrolledWindow3)
        bSizer2.Add(self.m_scrolledWindow3, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(bSizer2)
        self.Layout()
        self.Centre(wx.BOTH)

    def onOKButton(self, event):
        """Calls function registerAttributes """
        if self.mode == 'add':
            registerAttributes(self, self.class_attributes, self.class_type, mode=self.mode)
        elif self.mode == 'edit':
            #  create an empty object of the specified class
            object_to_edit = self.class_type.createEmptyObject()
            object_attributes = self.kwargs['object_attributes']

            i = 0
            for key in self.class_attributes:  # update the object with the data the user has input
                try:
                    if object_attributes[i] in ['', '-']:  # NULL value
                        object_attributes[i] = None
                except IndexError:  # in case some files have missing data at the end of the rows
                    object_attributes.append(None)
                attributeSetter(object_to_edit, key, object_attributes[i])
                i += 1
            registerAttributes(self, self.class_attributes, self.class_type, mode=self.mode,
                               object_to_edit=object_to_edit)

    def showDatatype(self, event):
        if self.m_menuItem2.IsChecked() == True:
            for item in self.datatype_label:
                item.Show()
        else:
            for item in self.datatype_label:
                item.Hide()

    def showOverride(self, event):
        if self.m_menuItem21.IsChecked() == True:
            for item in self.checkOverride:
                item.Show()
        else:
            for item in self.checkOverride:
                item.Hide()

    def overrideField(self, event):
        for item in self.checkOverride:
            if item.IsChecked() == True:
                #  print("Override content at %s" % self.checkOverride_event_Id_dict[item])
                override_attribute_dict[self.checkOverride_event_Id_dict[item]] = True
            elif item.IsChecked() == False:
                #  print("Do not override content at %s" % self.checkOverride_event_Id_dict[item])
                override_attribute_dict[self.checkOverride_event_Id_dict[item]] = False

    def openInfo(self, event):
        self.enable_toggle = False
        if self.enable_description == True:
            attribute = self.mouse_hover_Id_dict[event.Id]
            class_type_str = functions.getClass(str(self.class_type))
            self.info_dialog = infoDialog(self, "%s field description" % attribute,
                                          field_description_dict[class_type_str][attribute])
            self.info_dialog.Show()
        #  print(str(event.Id))

    def closeInfo(self, event):
        if self.enable_description == True and self.enable_toggle == False:
            self.info_dialog.Destroy()

    def doubleClick(self, event):
        self.enable_toggle = True

    def enableDescription(self, event):
        if self.m_menuItem3.IsChecked() == True:
            self.enable_description = True
        else:
            self.enable_description = False


class updatesuccessfulDialog(wx.Dialog):

    def __init__(self, parent):
        self.parent = parent

        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Update successful", pos=wx.DefaultPosition,
                           size=wx.Size(342, 182), style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        gSizer1 = wx.GridSizer(2, 1, 0, 0)

        self.m_panel2 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer6 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText8 = wx.StaticText(self.m_panel2, wx.ID_ANY, u"Update successful!", wx.DefaultPosition,
                                           wx.DefaultSize, wx.ALIGN_CENTRE)
        self.m_staticText8.Wrap(-1)
        self.m_staticText8.SetFont(
            wx.Font(22, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        bSizer6.Add(self.m_staticText8, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel2.SetSizer(bSizer6)
        self.m_panel2.Layout()
        bSizer6.Fit(self.m_panel2)
        gSizer1.Add(self.m_panel2, 1, wx.EXPAND | wx.ALL, 5)

        self.m_panel3 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.addAgain_button = wx.Button(self.m_panel3, wx.ID_ANY, u"Add another row", wx.DefaultPosition,
                                         wx.DefaultSize, 0)
        self.addAgain_button.SetFont(
            wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        bSizer7.Add(self.addAgain_button, 1, wx.ALL | wx.EXPAND, 5)

        self.cancel_button = wx.Button(self.m_panel3, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        self.cancel_button.SetFont(
            wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        bSizer7.Add(self.cancel_button, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel3.SetSizer(bSizer7)
        self.m_panel3.Layout()
        bSizer7.Fit(self.m_panel3)
        gSizer1.Add(self.m_panel3, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(gSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        self.addAgain_button.Bind(wx.EVT_BUTTON, self.addRow)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.closeWindows)

    def addRow(self, event):
        for textCtrl in self.parent.value_textCtrl:
            textCtrl.Value = ''
        self.Destroy()

    def closeWindows(self, event):
        self.parent.Destroy()
        self.Destroy()


class updateFailedDialog(wx.Dialog):

    def __init__(self, parent, error_message):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Update failed", pos=wx.DefaultPosition,
                           size=wx.Size(482, 324), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        fgSizer6 = wx.FlexGridSizer(3, 1, 5, 0)
        fgSizer6.AddGrowableCol(0)
        fgSizer6.AddGrowableRow(1)
        fgSizer6.SetFlexibleDirection(wx.BOTH)
        fgSizer6.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        self.m_staticText15 = wx.StaticText(self, wx.ID_ANY, u"Unable to update database", wx.DefaultPosition,
                                            wx.DefaultSize, 0)
        self.m_staticText15.Wrap(-1)
        self.m_staticText15.SetFont(
            wx.Font(20, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        fgSizer6.Add(self.m_staticText15, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.m_staticText16 = wx.StaticText(self, wx.ID_ANY, "The following error occured: " + error_message,
                                            wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText16.Wrap(-1)
        self.m_staticText16.SetFont(
            wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        fgSizer6.Add(self.m_staticText16, 0, wx.ALL | wx.EXPAND, 5)
        self.m_button15 = wx.Button(self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.Size(100, 30), 0)
        self.m_button15.SetFont(
            wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        fgSizer6.Add(self.m_button15, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SetSizer(fgSizer6)
        self.Layout()
        self.Centre(wx.BOTH)

        #  Connect Events
        self.m_button15.Bind(wx.EVT_BUTTON, self.closeWindow)

    def __del__(self):
        pass

    def closeWindow(self, event):
        self.Destroy()


class databaseSavedDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Database saved", pos=wx.DefaultPosition,
                           size=wx.Size(406, 201), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText5 = wx.StaticText(self, wx.ID_ANY, u"Database saved successfully", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.m_staticText5.Wrap(-1)
        self.m_staticText5.SetFont(
            wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))

        bSizer2.Add(self.m_staticText5, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.m_staticText6 = wx.StaticText(self, wx.ID_ANY, "Saved at %s" % saved_database_path,
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText6.Wrap(-1)
        bSizer2.Add(self.m_staticText6, 1, wx.ALL | wx.EXPAND, 5)

        self.m_button2 = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.m_button2, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.SetSizer(bSizer2)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        self.m_button2.Bind(wx.EVT_BUTTON, self.deleteSaveDialog)

    def __del__(self):
        pass

    def deleteSaveDialog(self, event):
        self.Destroy()


class importDatabaseDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Import Database", pos=wx.DefaultPosition,
                           size=wx.Size(461, 285), style=wx.CAPTION | wx.CLOSE_BOX | wx.STAY_ON_TOP)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        bSizer3 = wx.BoxSizer(wx.VERTICAL)

        self.m_panel2 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText7 = wx.StaticText(self.m_panel2, wx.ID_ANY,
                                           u"Enter the location (folder) of the desired database, then click OK:",
                                           wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText7.Wrap(-1)
        self.m_staticText7.SetFont(
            wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        bSizer4.Add(self.m_staticText7, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.m_panel2.SetSizer(bSizer4)
        self.m_panel2.Layout()
        bSizer4.Fit(self.m_panel2)
        bSizer3.Add(self.m_panel2, 1, wx.EXPAND | wx.ALL, 5)

        self.m_panel3 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer6 = wx.BoxSizer(wx.VERTICAL)

        self.location_picker = wx.DirPickerCtrl(self.m_panel3, wx.ID_ANY, wx.EmptyString, u"Select a folder",
                                                wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE)
        bSizer6.Add(self.location_picker, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel3.SetSizer(bSizer6)
        self.m_panel3.Layout()
        bSizer6.Fit(self.m_panel3)
        bSizer3.Add(self.m_panel3, 1, wx.EXPAND | wx.ALL, 5)

        self.m_panel4 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer7 = wx.BoxSizer(wx.HORIZONTAL)

        #  self.db_button = wx.Button
        #  ( self.m_panel4, wx.ID_ANY, u"Database file (db)",
        #  wx.DefaultPosition, wx.DefaultSize, 0 )

        #  self.db_button.SetFont
        #  ( wx.Font( 12, wx.FONTFAMILY_SWISS,
        #  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial" ) )

        #  bSizer7.Add( self.db_button, 1, wx.ALL|wx.EXPAND, 5 )

        self.txt_button = wx.Button(self.m_panel4, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        self.txt_button.SetFont(
            wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        bSizer7.Add(self.txt_button, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel4.SetSizer(bSizer7)
        self.m_panel4.Layout()
        bSizer7.Fit(self.m_panel4)
        bSizer3.Add(self.m_panel4, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(bSizer3)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        #  self.db_button.Bind( wx.EVT_BUTTON, self.importFromDB )
        self.txt_button.Bind(wx.EVT_BUTTON, self.importFromTXT)

    #  Virtual event handlers, override them in your derived class
    def importFromTXT(self, event):
        if self.location_picker.Path == '':
            pass
        else:
            global imported_database_path
            imported_database_path = self.location_picker.Path
            print("Opening database files at %s..." % imported_database_path)
            #  Create database file (only the schema is loaded)
            try:
                os.remove(imported_database_path + '/database.db')
                print("Database file overwritten.")
            except FileNotFoundError:
                print("Database file created.")
            global engine
            #  createConnection(imported_database_path + "\\database.db")
            #  engine = sqlalchemy.create_engine
            #  ('sqlite:///' + imported_database_path.replace('\\', '/') + '/database.db', echo=False)
            createConnection(':memory:')
            engine = sqlalchemy.create_engine('sqlite:///:memory:', echo=False)
            Base.metadata.create_all(engine)
            Session = sqlalchemy.orm.sessionmaker(bind=engine)

            global session
            session = Session()
            self.Destroy()

            #  closes main frame
            try:  # in case it doesn't exist
                main_frame.Destroy()
            except:
                pass

            #  Set progress dialog
            global size_dict
            max_size, size_dict = functions.setProgressBar(imported_database_path)
            global load_progress_dialog
            load_progress_dialog = progressDialog(self, max_size, 'Loading data from files...')
            load_progress_dialog.Show()

            #  Load data from txt files onto database file
            loadFromTXT()

            #  Open workspace frame
            global workspace_frame
            workspace_frame = workspaceFrame(None)
            workspace_frame.Show()

    def importFromDB(self, event):
        """
        Import from .db file. **ATTENTION: THE SCHEMA OF THE IMPORTED DATABASE WILL
        BE THE UNE USED.
        """
        print("Import from .db file is not supported.")


class savingLocationDialog(wx.Dialog):
    """
    Prompts the user to enter the location where the database is to be saved. If no location is entered,
    the default location will be chosen.
    """

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Saving location", pos=wx.DefaultPosition,
                           size=wx.Size(461, 285), style=wx.CAPTION | wx.CLOSE_BOX | wx.STAY_ON_TOP)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer3 = wx.BoxSizer(wx.VERTICAL)

        self.m_panel2 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText7 = wx.StaticText(self.m_panel2, wx.ID_ANY,
                                           u"Enter the location where the database is to be saved:", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        self.m_staticText7.Wrap(-1)
        self.m_staticText7.SetFont(
            wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        bSizer4.Add(self.m_staticText7, 1, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.m_panel2.SetSizer(bSizer4)
        self.m_panel2.Layout()
        bSizer4.Fit(self.m_panel2)
        bSizer3.Add(self.m_panel2, 1, wx.EXPAND | wx.ALL, 5)

        self.m_panel3 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer6 = wx.BoxSizer(wx.VERTICAL)

        self.location_picker = wx.DirPickerCtrl(self.m_panel3, wx.ID_ANY, wx.EmptyString, u"Select a folder",
                                                wx.DefaultPosition, wx.DefaultSize, wx.DIRP_USE_TEXTCTRL)
        bSizer6.Add(self.location_picker, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel3.SetSizer(bSizer6)
        self.m_panel3.Layout()
        bSizer6.Fit(self.m_panel3)
        bSizer3.Add(self.m_panel3, 1, wx.EXPAND | wx.ALL, 5)

        self.m_panel4 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.save_button = wx.Button(self.m_panel4, wx.ID_ANY, u"Change location", wx.DefaultPosition, wx.DefaultSize,
                                     0)
        self.save_button.SetFont(
            wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))

        bSizer7.Add(self.save_button, 1, wx.ALL | wx.EXPAND, 5)

        self.m_panel4.SetSizer(bSizer7)
        self.m_panel4.Layout()
        bSizer7.Fit(self.m_panel4)
        bSizer3.Add(self.m_panel4, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(bSizer3)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        self.save_button.Bind(wx.EVT_BUTTON, self.saveDatabase)

    #  Virtual event handlers, override them in your derived class
    def saveDatabase(self, event):
        if self.location_picker.Path == '':
            pass
        else:
            global saved_database_path
            saved_database_path = self.location_picker.Path
            global imported_database_path
            imported_database_path = saved_database_path
            self.Destroy()
            print("Saving directory changed to %s" % saved_database_path)
            try:
                main_frame.createNewDatabase()
            except NameError:  # in case the user just wants to change the location
                pass


class deleteRowDialog(wx.Dialog):

    def __init__(self, parent):
        self.parent = parent

        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Delete row", pos=wx.DefaultPosition,
                           size=wx.Size(440, 267), style=wx.CAPTION | wx.STAY_ON_TOP)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        gSizer5 = wx.GridSizer(2, 1, 0, 5)
        text = 'Row to be deleted: ' + str(parent.selected_object_attributes)

        self.m_staticText12 = wx.StaticText(self, wx.ID_ANY, text, wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText12.Wrap(-1)
        self.m_staticText12.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        gSizer5.Add(self.m_staticText12, 0, wx.ALL | wx.EXPAND, 5)

        bSizer181 = wx.BoxSizer(wx.HORIZONTAL)

        self.Ok_button = wx.Button(self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        self.Ok_button.SetFont(
            wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        bSizer181.Add(self.Ok_button, 1, wx.ALL | wx.EXPAND, 5)

        self.cancel_button = wx.Button(self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        self.cancel_button.SetFont(
            wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        bSizer181.Add(self.cancel_button, 1, wx.ALL | wx.EXPAND, 5)

        gSizer5.Add(bSizer181, 1, wx.EXPAND, 5)

        self.SetSizer(gSizer5)
        self.Layout()

        self.Centre(wx.BOTH)

        #  Connect Events
        self.Ok_button.Bind(wx.EVT_BUTTON, self.proceed)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.cancel)
        self.Bind(wx.EVT_CLOSE, self.enableSelect)
        self.Bind(wx.EVT_INIT_DIALOG, self.disableSelect)

    #  Virtual event handlers, override them in your derived class
    def proceed(self, event):
        registerAttributes(None, self.parent.selected_class_attributes, self.parent.tab_class_type,
                           self.parent.selected_object_attributes, mode='delete')
        self.Destroy()
        self.enableSelect(None)

    def cancel(self, event):
        self.Destroy()

    def enableSelect(self, event):
        self.parent.enable_select = True

    def disableSelect(self, event):
        self.parent.enable_select = False


class infoDialog(wx.Dialog):

    def __init__(self, parent, Title, info):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=Title, pos=wx.DefaultPosition, size=wx.Size(500, 350),
                           style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer9 = wx.BoxSizer(wx.VERTICAL)

        self.m_scrolledWindow3 = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL)
        self.m_scrolledWindow3.SetScrollRate(5, 5)
        bSizer10 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText14 = wx.StaticText(self.m_scrolledWindow3, wx.ID_ANY, info, wx.DefaultPosition, wx.DefaultSize,
                                            0)
        self.m_staticText14.Wrap(390)
        self.m_staticText14.SetFont(
            wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        bSizer10.Add(self.m_staticText14, 1, wx.ALL | wx.EXPAND, 5)

        self.m_scrolledWindow3.SetSizer(bSizer10)
        self.m_scrolledWindow3.Layout()
        bSizer10.Fit(self.m_scrolledWindow3)
        bSizer9.Add(self.m_scrolledWindow3, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(bSizer9)
        self.Layout()

        self.Centre(wx.BOTH)


class progressDialog(wx.Dialog):
    def __init__(self, parent, max_progress, label):
        self.max_progress = max_progress
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"work in progress", pos=wx.DefaultPosition,
                           size=wx.Size(417, 187), style=wx.DEFAULT_DIALOG_STYLE)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)
        gSizer10 = wx.GridSizer(2, 1, 0, 5)

        print(label)
        self.label_text = wx.StaticText(self, wx.ID_ANY, label, wx.DefaultPosition, wx.DefaultSize, 0)
        self.label_text.Wrap(-1)
        self.label_text.SetFont(
            wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString))

        gSizer10.Add(self.label_text, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        self.progress_bar = wx.Gauge(self, wx.ID_ANY, max_progress, wx.DefaultPosition, wx.DefaultSize,
                                     wx.GA_HORIZONTAL | wx.GA_SMOOTH)
        self.progress_bar.SetValue(0)
        gSizer10.Add(self.progress_bar, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(gSizer10)
        self.Layout()

        self.Centre(wx.BOTH)

    def updateProgress(self, gap):
        """updates the progress bar with the specified leap."""
        current_progress = self.progress_bar.GetValue()
        value = gap + current_progress
        self.progress_bar.SetValue(value)
        progress = 100 * self.progress_bar.GetValue() / self.max_progress
        print("Progress: %.2f %%" % progress)


def loadFromTXT():
    """Loads data from txt files onto database file"""
    files_list = os.listdir(imported_database_path)
    locations_list = []
    for i in range(len(files_list)):
        locations_list.append(imported_database_path + "\\" + files_list[i])

    table_iterator = 0
    for table in suggested_input_order:
        if table not in not_supported_tables:
            table_path = functions.getPath(table, imported_database_path)
            if table_path in locations_list:  # available files that support tables
                column_names = functions.getColumnNames(tablename_dict[table])[0]
                n_rows, n_columns = functions.getRowsAndcolumns(tablename_dict[table], imported_database_path)
                rows_data = functions.getRowDataFromFiles(tablename_dict[table], n_rows - 1, imported_database_path)

                #  Force values to be entered into the database
                global override_attribute_dict
                override_attribute_dict = {}

                # dictionary associating each attribute with its corresponding maximum length
                attribute_maxlen_dict = {}

                # dictionary associating each attribute with its corresponding data type
                attribute_datatype_dict = {}
                for column_name in column_names:
                    override_attribute_dict.update({column_name: True})
                    datatype, max_len = functions.getDatatypeAndLength(table, column_name)
                    attribute_maxlen_dict.update({column_name: max_len})

                #  attribute_datatype_dict.update({column_name : datatype})
                row_iterator = 0
                for row in rows_data:
                    if len(row) > len(column_names):
                        row = row[0: len(column_names)]

                    column_iterator = 0
                    for value in row:  # shortens values to fit in database SQL
                        column_name = column_names[column_iterator]

                        if value != None:
                            if len(value) > attribute_maxlen_dict[column_name]:
                                row[column_iterator] = value[0:attribute_maxlen_dict[column_name]]
                        column_iterator += 1

                    registerAttributes(None, column_names, tablename_dict[table], row, mode='add_fromTXT')
                    row_iterator += 1

            #  update progress
            try:
                load_progress_dialog.updateProgress(size_dict[table])
            except KeyError:  # in case there is no such file
                pass
    else:
        print("Import finished")


def registerAttributes(current_add_frame, class_attributes, class_type, *args, **kwargs):
    """
    Stores the values input by the user into an object of the chosen class, then saves database.
    Input:	current_add_frame: addFrame from which the function was called (if exists).
            class attributes: list with the column names.
            class_type: class type as class.
            optional positional argument: object attributes (when applicable), object to edit (when appliccable)
            compulsory keyword arguments: mode (add_fromTXT/ add/ edit/ delete)
    """

    # object attributes are passed directly.
    if current_add_frame == None:
        object_attributes = args[0]

    # values should be retrieved from the interaction with the user (textCtrl)
    else:
        object_attributes = []
        for i in range(len(class_attributes)):  # store input values
            object_attributes.append(current_add_frame.value_textCtrl[i].Value)

    #  create an empty object of the specified class
    object_to_change = class_type.createEmptyObject()

    #  if class_type == PID:
    #  	print("Stop debugger")

    i = 0
    # update the object with the data the user has input (or the data already in the table)
    for key in class_attributes:
        try:
            if object_attributes[i] in ['', '-']:  # NULL value
                object_attributes[i] = None
        except IndexError:  # in case some files have missing data at the end of the rows
            object_attributes.append(None)
        attributeSetter(object_to_change, key, object_attributes[i])
        i += 1

    #  check for errors and constraints, update database
    if kwargs['mode'] == 'add_fromTXT':
        object_to_change_updated = functions.setDefaultValues(functions.getClass(str(class_type)), object_to_change)
        try:
            sqlalchemy.orm.session.make_transient(object_to_change_updated)
            session.add(object_to_change_updated)
            session.commit()
        except sqlalchemy.exc.IntegrityError:
            print("Integrity error. Row not imported.")
        finally:
            session.rollback()
    elif kwargs['mode'] == 'add':
        success, error_message = updateDatabase(object_to_change, class_type, class_attributes, object_attributes,
                                                mode='add')
    elif kwargs['mode'] == 'edit':
        success, error_message = updateDatabase(kwargs['object_to_edit'], class_type, class_attributes,
                                                object_attributes, mode='edit')
        #  update all tables, as deleting a parent object can delete subsequent children.
        for table in tablename_list:
            if table not in not_supported_tables:
                if workspace_frame.table_grid[table].GetNumberRows() != session.query(
                        tablename_dict[table]).count():  # only do if number of rows has changed
                    workspace_frame.updateTable(table)
                    print("%s table updated" % table)
    elif kwargs['mode'] == 'delete':
        for item in session.query(class_type).all():  # looks in the database for the object to delete
            if item == object_to_change:
                #  print("%s object found" % str(object_to_change))
                success = True
                session.delete(item)
                try:
                    session.commit()
                except:
                    session.rollback()
                break

        #  update all tables, as deleting a parent object can delet subsequent children.
        for table in tablename_list:
            if table not in not_supported_tables:
                if workspace_frame.table_grid[table].GetNumberRows() != session.query(
                        tablename_dict[table]).count():  # only do if number of rows has changed
                    workspace_frame.updateTable(table)
                    print("%s table updated" % table)
        else:
            success = False
            error_message = "\n %s object not found" % str(object_to_change)

    # only applies if the user has input the values
    if current_add_frame != None:
        if success:  # Update successful
            current_add_frame.update_dialog = updatesuccessfulDialog(current_add_frame)  # shows a dialog
            current_add_frame.update_dialog.Show()
            #  update table
            for key, value in tablename_dict.items():
                if value == class_type:
                    break
            workspace_frame.updateTable(key)
        else:
            current_add_frame.update_dialog = updateFailedDialog(current_add_frame, error_message)
            current_add_frame.update_dialog.Show()


def updateDatabase(object_to_add, class_type_noformat, class_attributes, object_attributes, **kwargs):
    """
        Adds the objects to the database.
        Returns a tuple with the first parameter being True if the update is successful
        and the second being a message to be displayed
        Input:	object_to_add: object.
                class_type_noformat: class type, it doesn't matter which format.
                class attributes: list with the class attributes.
                object_attributes: list with the object attributes.
                compulsory keyword arguments: mode (add/ edit).
    """
    try:
        if kwargs['mode'] == 'add':
            session.add(object_to_add)  # Checks database constraints
            session.commit()
            session.delete(object_to_add)
            session.commit()
            #  session.delete(object_to_add)
            #  session.commit()
            object_to_add_updated = functions.checkRuntimeConstraints(object_to_add, class_type_noformat,
                                                                      class_attributes, object_attributes, session,
                                                                      override_attribute_dict)  # Checks runtime constraints
            #  sqlalchemy.orm.session.make_transient(object_to_add)
            sqlalchemy.orm.session.make_transient(object_to_add_updated)
            session.add(object_to_add_updated)
            session.commit()
        elif kwargs['mode'] == 'edit':
            """
            object_attributes: new ones (list)
            object_to_add: former row
            object_to_add_updated: new row 
            object_to add_corrected: new row with default values
            """

            class_type = tablename_dict[functions.getClass(class_type_noformat)]
            query1 = session.query(class_type)
            for item in query1:  # select row to update
                if item == object_to_add:
                    for key, value in class_type.__dict__.items():
                        if key in class_attributes:
                            query1 = query1.filter(value == object_to_add.__dict__[key])
                    break

            #  create an empty object of the specified class
            object_to_add_updated = class_type.createEmptyObject()
            i = 0
            for key in class_attributes:  # update the object with the data the user has input
                try:
                    if object_attributes[i] in ['', '-']:  # NULL value
                        object_attributes[i] = None
                except IndexError:  # in case some files have missing data at the end of the rows
                    object_attributes.append(None)
                attributeSetter(object_to_add_updated, key, object_attributes[i])
                i += 1

            object_to_add_corrected = functions.checkRuntimeConstraints(object_to_add_updated, class_type_noformat,
                                                                        class_attributes, object_attributes, session,
                                                                        override_attribute_dict)  # Checks runtime constraints
            #  update row
            update_dict = {}
            for field in class_attributes:
                former_value = object_to_add.__dict__[field]
                new_value = object_to_add_corrected.__dict__[field]
                if new_value != former_value:
                    update_dict.update({field: new_value})
            query1.update(update_dict, synchronize_session=False)
            session.commit()
    except sqlalchemy.exc.IntegrityError as exc:
        cause = str(exc.__cause__)
        try:
            failed_constraint = cause.split(" constraint failed: ")[0]
            position = cause.split(" constraint failed: ")[1]

            # UNIQUE constraint failed. Note that there could be a composite primary key
            if failed_constraint == 'UNIQUE':
                message = "Primary key at %s is not unique" % position
            elif failed_constraint == 'CHECK':
                message = "Exceeded allowed field length or datatype mismatch at %s" % position
            else:
                message = str(cause)
        except:
            message = str(exc.__cause__)

        print(exc)
        return_tuple = (False, message)
    except sqlalchemy.orm.exc.FlushError as exc:
        cause = str(exc.__cause__)
        print(exc)
        return_tuple = (False, exc.message)
    except ValueError as exc:
        message = "Datatype mismatch"
        print(exc)
        return_tuple = (False, message)
    except functions.RunTimeError as exc:
        print(exc)
        return_tuple = (False, exc.message)
    except BaseException as exc:
        print(exc)
        message = str(type(exc)) + str(exc)
        return_tuple = (False, message)
    else:
        print("%s row updated successfully" % str(type(object_to_add)))
        return_tuple = (True, None)
    finally:
        session.rollback()
        return return_tuple


def createConnection(db_file):
    """ create a database connection to a SQLite database """
    global conn
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    #  print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app = wx.App()
    main_frame = mainFrame(None)
    main_frame.Show()
    app.MainLoop()
