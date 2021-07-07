import time
import os
from datetime import datetime
import wx
import wx.xrc
import wx.aui
import wx.grid
from schema import *
import functions
import sqlite3
import sqlalchemy
from data_extractor import data_info_dict as field_description_dict


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
                # Force values to be entered into the database
                global override_attribute_dict
                override_attribute_dict = {}
                attribute_maxlen_dict = {}  # dictionary associating each attribute with its corresponding maximum length
                attribute_datatype_dict = {}  # dictionary associating each attribute with its corresponding data type
                for column_name in column_names:
                    override_attribute_dict.update({column_name: True})
                    datatype, max_len = functions.getDatatypeAndLength(table, column_name)
                    attribute_maxlen_dict.update({column_name: max_len})
                # attribute_datatype_dict.update({column_name : datatype})

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
            # update progress
            try:
                load_progress_dialog.updateProgress(size_dict[table])
            except KeyError:  # in case there is no such file
                pass
    else:
        print("Import finished")


def registerAttributes(current_add_frame, class_attributes, class_type, *args, **kwargs):
    """Stores the values input by the user into an object of the chosen class, then saves database.
	Input:	current_add_frame: addFrame from which the function was called (if exists).
			class attributes: list with the column names.
			class_type: class type as class.
			optional positional argument: object attributes (when applicable), object to edit (when appliccable)
			compulsory keyword arguments: mode (add_fromTXT/ add/ edit/ delete)"""

    if current_add_frame == None:  # object attributes are passed directly.
        object_attributes = args[0]
    else:  # values should be retrieved from the interaction with the user (textCtrl)
        object_attributes = []
        for i in range(len(class_attributes)):  # store input values
            object_attributes.append(current_add_frame.value_textCtrl[i].Value)

    # create an empty object of the specified class
    object_to_change = class_type.createEmptyObject()

    # if class_type == PID:
    # 	print("Stop debugger")

    i = 0
    for key in class_attributes:  # update the object with the data the user has input (or the data already in the table)
        try:
            if object_attributes[i] in ['', '-']:  # NULL value
                object_attributes[i] = None
        except IndexError:  # in case some files have missing data at the end of the rows
            object_attributes.append(None)
        attributeSetter(object_to_change, key, object_attributes[i])
        i += 1

    # check for errors and constraints, update database
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
        # update all tables, as deleting a parent object can delet subsequent children.
        for table in tablename_list:
            if table not in not_supported_tables:
                if workspace_frame.table_grid[table].GetNumberRows() != session.query(
                        tablename_dict[table]).count():  # only do if number of rows has changed
                    workspace_frame.updateTable(table)
                    print("%s table updated" % table)
    elif kwargs['mode'] == 'delete':
        for item in session.query(class_type).all():  # looks in the database for the object to delete
            if item == object_to_change:
                # print("%s object found" % str(object_to_change))
                success = True
                session.delete(item)
                try:
                    session.commit()
                except:
                    session.rollback()
                break
        # update all tables, as deleting a parent object can delet subsequent children.
        for table in tablename_list:
            if table not in not_supported_tables:
                if workspace_frame.table_grid[table].GetNumberRows() != session.query(
                        tablename_dict[table]).count():  # only do if number of rows has changed
                    workspace_frame.updateTable(table)
                    print("%s table updated" % table)
        else:
            success = False
            error_message = "\n %s object not found" % str(object_to_change)

    if current_add_frame != None:  # only applies if the user has input the values
        if success:  # Update successful
            current_add_frame.update_dialog = updatesuccessfulDialog(current_add_frame)  # shows a dialog
            current_add_frame.update_dialog.Show()
            # update table
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
	and the second being a message to be diplayed
	Input:	object_to_add: object.
			class_type_noformat: class type, it doesn't matter which format.
			class attributes: list with the class attributes.
			object_attributes: list with the object attributes.
			compulsory keyword arguments: mode (add/ edit)."""
    try:
        if kwargs['mode'] == 'add':
            session.add(object_to_add)  # Checks database constraints
            session.commit()
            session.delete(object_to_add)
            session.commit()
            # session.delete(object_to_add)
            # session.commit()
            object_to_add_updated = functions.checkRuntimeConstraints(object_to_add, class_type_noformat,
                                                                      class_attributes, object_attributes, session,
                                                                      override_attribute_dict)  # Checks runtime constraints
            # sqlalchemy.orm.session.make_transient(object_to_add)
            sqlalchemy.orm.session.make_transient(object_to_add_updated)
            session.add(object_to_add_updated)
            session.commit()
        elif kwargs['mode'] == 'edit':
            """
            object_attributes: new ones (list)
            object_to_add: former row
			object_to_add_updated: new row 
			object_to add_corrected: new row with default values"""
            class_type = tablename_dict[functions.getClass(class_type_noformat)]
            query1 = session.query(class_type)
            for item in query1:  # select row to update
                if item == object_to_add:
                    for key, value in class_type.__dict__.items():
                        if key in class_attributes:
                            query1 = query1.filter(value == object_to_add.__dict__[key])
                    break

            # create an empty object of the specified class
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
            # update row
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
            if failed_constraint == 'UNIQUE':  # UNIQUE constraint failed. Note that there could be a composite primary key
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
    # print(sqlite3.version)
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()
