location_MIB_ejemplo_sener = "C:\\Users\\andres.miguelez\\Documents\\MIB ejemplo\\"
location_MIB_ejemplo_hp = "C:\\facil_acceso\\SENER\\MIB ejemplo\\ASCII\\"
location_MIB_real_sener = "C:\\Users\\andres.miguelez\\Documents\\MIB_real\\"
location_MIB_real_hp = "C:\\facil_acceso\\SENER\\MIB_real\\"

import schema
from sqlalchemy import *
from sqlalchemy.orm import make_transient
from sqlalchemy.orm import sessionmaker
import sqlite3
import os
import sys
import time
from operator import itemgetter, attrgetter


class InexistentVDFTableError(Exception):
    """VDF table is mandatory"""

    def __init__(self):
        print("VDF table is mandatory")


class RunTimeError(Exception):
    """Exception raised when checking constraints at run time."""

    def __init__(self, field, value):
        self.field = str(field)
        self.table = str(field).split('_')[0] + '_table'
        self.value = str(value)

    def __str__(self):
        return "Invalid value ('%s') at %s in %s" % (self.value, self.field, self.table)


class InvalidAttributeError(RunTimeError):
    """
    To be raised when run-time constraints are checked. Only appliccable to strings.
    Not_applicable indicates that a field is not applicable to the table due to other conditions
    """

    def __init__(self, field, value, kwargs):
        super().__init__(field, value)
        if 'full_message' in kwargs:
            self.message = kwargs['full_message']
        else:
            if kwargs['not_applicable']:
                self.message = "%s is not applicable" % field
            else:
                self.message = "Invalid value ('%s') at %s" % (value, field)


class IntegerAttributeOutOfRangeError(RunTimeError):
    """To be raised when run-time constraints are checked. Only applicable to integers."""

    def __init__(self, field, value):
        super().__init__(field, value)
        self.message = "Value ('%s') out of range at %s" % (str(value), field)


class UnmatchingForeignKeyError(RunTimeError):
    """to be raised a run-time when a field should match another in a foreign table."""

    def __init__(self, field, value, foreign_key, foreign_key_table):
        super().__init__(field, value)
        self.message = "Field %s ('%s') does not match any value in column %s at %s" % (
            str(field), str(value), str(foreign_key), str(foreign_key_table))


class RunTimeUnraisedError:
    """Does pretty much the same as the Error but it does not raise one"""

    def __init__(self, field, value):
        self.field = str(field)
        self.table = str(field).split('_')[0] + '_table'
        self.value = str(value)
        global error_log
        error_log.append(self)


class InvalidAttribute(RunTimeUnraisedError):
    def __init__(self, field, value, **kwargs):
        super().__init__(field, value)
        self.kwargs = kwargs

    def raiseException(self):
        raise InvalidAttributeError(self.field, self.value, self.kwargs)


class IntegerAttributeOutOfRange(RunTimeUnraisedError):
    def __init__(self, field, value):
        super().__init__(field, value)

    def raiseException(self):
        raise IntegerAttributeOutOfRangeError(self.field, self.value)


class UnmatchingForeignKey(RunTimeUnraisedError):
    def __init__(self, field, value, foreign_key, foreign_key_table):
        super().__init__(field, value)
        self.foreign_key = foreign_key
        self.foreign_key_table = foreign_key_table

    def raiseException(self):
        raise UnmatchingForeignKeyError(self.field, self.value, self.foreign_key, self.foreign_key_table)


def getPath(class_type_noformat, folder_path):
    """
    Returns the path of the specified table. For example tables, folder_path
    should be set to None. Input class_type_noformat as either string or class
    """

    files = os.listdir(folder_path)
    for filename in files:
        if filename.split('.')[0].lower() == 'vdf':  # vdf file is compulsory
            global file_extension
            file_extension = '.%s' % filename.split('.')[-1]
            break

    file_list = []
    for filename in files:
        if filename.split(file_extension)[0].upper() in schema.tablename_list:
            file_list.append(filename.split(file_extension)[0])

    if type(class_type_noformat) == str:
        return folder_path + "\\" + str(class_type_noformat).lower() + file_extension
    else:
        a = str(class_type_noformat)
        a = a.replace("<class 'schema.", '')
        a = a.replace("'>", "")
        return folder_path + "\\" + a.lower() + file_extension


def getRowsAndcolumns(class_type, folder_path):
    """
    returns number of rows (INCLUDING header) and columns
    of the specified table (.dat or .txt file). For example tables, folder_path
    should be set to None. Input class_type	as either string or class.
    """

    path = getPath(class_type, folder_path)
    class_type_str = getClass(str(class_type))
    try:
        file = open(path, "r")
    except FileNotFoundError:
        print("File %s does not exist." % class_type_str)
        n_rows = -1
        n_columns = 0
    else:
        file.seek(0)
        n_rows = len(file.readlines())
        file.seek(0)

        if n_rows == 0:
            n_rows = -1
            n_columns = 0
        else:
            for i in range(n_rows):
                line = file.readline()
                parameters = line.split("\t")
                parameters[-1] = parameters[-1].replace("\n", "")

            n_columns = len(parameters)

        file.close()
    finally:
        return n_rows + 1, n_columns


def getColumnNames(class_type):
    """
    Returns a list with the column names of the specified class, a dictionary indicating
    weather the attribute is nullable and a dictionary with the attribute's foreign key.
    Input class_type as a class.
    Output: The foreign key dictionary contains a key for each column of the table at hand. If that column
    is not to be treated as a foreign key, the value is None. If that column is to be treated as a foreign key,
    the value is a list, with each element being a foreign key. Each element contains a dictionary, with the
    table and field of the foreign key.
    """

    dictionary = class_type.__dict__
    atrribute_list = []
    nullable_key_dict = {}
    foreign_keys_dict = {}
    for key, value in dictionary.items():
        if key.split('_')[0] == class_type.__tablename__.split('_')[0]:
            atrribute_list.append(key)
            nullable_key_dict.update({key: value.expression.nullable})
            # print(value.expression.foreign_keys)
            if len(value.expression.foreign_keys) == 0:
                foreign_keys_dict.update({key: None})
            else:
                fk_list = []
                for fk in value.expression.foreign_keys:
                    fk_data = {
                        "table": fk._column_tokens[1].split('_table')[0],  # class as string
                        "field": fk._column_tokens[2]  # field as a string
                    }
                    fk_list.append(fk_data)
                foreign_keys_dict.update({key: fk_list})

    return atrribute_list, nullable_key_dict, foreign_keys_dict


def getRowDataFromDB(class_type, session):
    """
    returns a list of lists with the fields of each row. Rows are extracted from database.
    Empty fields are represented with a dash.
    Input: class type as class
    """

    column_names = getColumnNames(class_type)[0]
    complete_table = []
    row_list = session.query(class_type).all()

    i = 0
    for row in row_list:
        complete_table.append([])
        values = row.__dict__
        for column_name in column_names:
            value = values[column_name]
            if value is None:
                complete_table[i].append('-')
            else:
                complete_table[i].append(str(value))

        i += 1

    return sortTableData(complete_table, class_type)


def getRowDataFromFiles(class_type_noformat, n_rows, folder_path):
    """
    returns a list of lists with the fields of each row.
    Empty fields are represented with a dash. For example tables, folder_path
    should be set to None. Input class_type_noformat	as either string or class.
    """

    path = getPath(class_type_noformat, folder_path)
    class_type = getClass(str(class_type_noformat))

    try:
        file = open(path, "r")
    except FileNotFoundError:
        complete_table = []
    else:
        file.seek(0)
        complete_table = []
        for column in range(n_rows):
            line = file.readline()
            parameters = line.split("\t")
            parameters[-1] = parameters[-1].replace("\n", "")
            i = 0
            for item in parameters:
                if item in ['', None]:
                    parameters[i] = '-'
                i += 1
            complete_table.append(parameters)
        file.close()
    finally:
        return sortTableData(complete_table, class_type)


def exportDatabase(engine, session, path, new_database):
    """
    Exports the database file (.db) to texts files (one per table) at chosen location
    Input: 	path: path where the text files will be stored
    new_database: indicates whether the database is to be created from scratch.
    """
    # create working directory
    # path += "\\exported_database"
    try:
        os.mkdir(path)
    except FileExistsError:
        # print("Directory %s already exists" %path) """obsolete"""
        pass
    else:
        print("Successfully created the directory %s " % path)

    inspector = inspect(engine)

    # check if VDF table exists
    for table_name in inspector.get_table_names():
        class_type_str = table_name.split('_table')[0]
        if class_type_str in schema.tablename_list:  # avoids mapping tables
            try:
                class_type = schema.tablename_dict[class_type_str]
            except KeyError:  # omits association tables
                pass
            if table_name == 'VDF_table' and len(session.query(class_type).all()) == 0 and new_database == False:
                print("VDF table is compulsory. Currently, there is no such table")
    for table_name in inspector.get_table_names():
        class_type_str = table_name.split('_table')[0]
        try:
            class_type = schema.tablename_dict[class_type_str]
        except KeyError:  # omits association tables
            continue

        # create file
        arc = open(path + "\\" + class_type_str.lower() + '.txt', 'w')

        row_list = session.query(class_type).all()
        for row in row_list:
            column_names = (row.__class__).__dict__.keys()
            first_column = True  # once per row
            for column_name in column_names:
                if column_name.split('_')[0] == class_type_str:
                    value = row.__dict__[column_name]
                    # print(column_name, value)
                    if first_column:
                        if value is None:
                            arc.write("\t")
                        else:
                            arc.write(str(value))
                            first_column = False
                    else:
                        if value is None:
                            arc.write("\t")
                        else:
                            arc.write("\t" + str(value))
            arc.write("\n")

        arc.close()

    return path


def getClass(s):
    """Enter a string, returns class type as string"""
    s = str(s)
    if 'schema' in s:
        class_type = s.split('.')[-1].split("'>")[0]
    elif '__main__' in s:
        class_type = s.split('.')[-1].split("'>")[0]
    elif "'" in s:
        class_type = s.replace("'", "").replace(" ", "")
    elif '"' in s:
        class_type = s.replace('"', "").replace(" ", "")
    else:
        class_type = s

    return class_type.upper()


def getDatatypeAndLength(class_type_noformat, class_attribute):
    """
    Returns a tuple indicating the datatype and maximum allowed
        length of a table class_attribute.
        Input: 	Class type as desired.
        Class attribute as a string.
    """

    class_type = schema.tablename_dict[getClass(class_type_noformat)]
    for attribute, value in class_type.__dict__.items():
        if attribute == class_attribute:
            if str(value.type)[0:3].lower() == 'var':  # String
                datatype = "String"
            elif str(value.type)[0:3].lower() == 'int':  # Integer
                datatype = "Integer"

            if datatype == 'String':
                max_len = value.type.length
            elif datatype == 'Integer':
                max_len = class_type.integer_maxlen[str(value).split('.')[-1]]

            if max_len is None:
                max_len = sys.maxsize
            break

    return datatype, max_len


def createAttributeDictionary(class_type_noformat, class_attributes, object_attributes):
    """
    Creates a dictionary with the column names and values of a row.
    Changes blank spaces to either 0 (for integers) of empty strings (for strings).
    """

    attributes_dictionary = {}
    for i in range(len(class_attributes)):
        datatype, max_len = getDatatypeAndLength(class_type_noformat, class_attributes[i])

        if object_attributes[i] is None:
            if datatype == 'String':
                attributes_dictionary.update({class_attributes[i]: ''})
            elif datatype == 'Integer':
                attributes_dictionary.update({class_attributes[i]: 0})
        else:
            if datatype == 'String':
                attributes_dictionary.update({class_attributes[i]: object_attributes[i]})
            elif datatype == 'Integer':
                attributes_dictionary.update({class_attributes[i]: int(object_attributes[i])})  # casts value to integer

    return attributes_dictionary


def checkRuntimeConstraints(object_to_update, class_type_noformat, class_attributes, object_attributes, session,
                            override_attribute_dict):
    """
    Checks other constraints and sets default values when a row is added into a table
    Input:	Object to be checked.
            Class type. Doesn't matter the format.
            Class attributes as a string.
            Object attributes as a string.
            Session.
            Dictionary containing the attributes where exceptions should not be considered.
    """

    class_type_str = getClass(class_type_noformat)

    attributes_dictionary = createAttributeDictionary(class_type_str, class_attributes,
                                                      object_attributes)  # Creates a dictionary with the attributes

    # initialise error log: stores all the broken run time constraints
    global error_log
    error_log = []

    if class_type_str == "DPF":
        if attributes_dictionary["DPF_TYPE"] not in ['1', '3']:
            InvalidAttribute("DPF_TYPE", attributes_dictionary["DPF_TYPE"], not_applicable=False)

    elif class_type_str == "GPF":
        if attributes_dictionary["GPF_TYPE"] not in ['F', 'H', 'Q', 'S']:
            InvalidAttribute("GPF_TYPE", attributes_dictionary["GPF_TYPE"], not_applicable=False)
        if attributes_dictionary["GPF_SCROL"] not in ['Y', 'N'] and attributes_dictionary["GPF_SCROL"] != '':
            InvalidAttribute("GPF_SCROL", attributes_dictionary["GPF_SCROL"], not_applicable=False)
        if attributes_dictionary["GPF_HCOPY"] not in ['Y', 'N'] and attributes_dictionary["GPF_HCOPY"] != '':
            InvalidAttribute("GPF_HCOPY", attributes_dictionary["GPF_HCOPY"], not_applicable=False)
        if int(attributes_dictionary["GPF_DAYS"]) < 0 or int(attributes_dictionary["GPF_DAYS"]) > 99:
            IntegerAttributeOutOfRange("GPF_DAYS", attributes_dictionary["GPF_DAYS"])
        if int(attributes_dictionary["GPF_HOURS"]) < 0 or int(attributes_dictionary["GPF_HOURS"]) > 23:
            IntegerAttributeOutOfRange("GPF_HOURS", attributes_dictionary["GPF_HOURS"])
        if int(attributes_dictionary["GPF_MINUT"]) < 0 or int(attributes_dictionary["GPF_MINUT"]) > 59:
            IntegerAttributeOutOfRange("GPF_MINUT", attributes_dictionary["GPF_MINUT"])
        if attributes_dictionary["GPF_AXCLR"] not in ['1', '2', '3', '4', '5', '6', '7']:
            InvalidAttribute("GPF_AXCLR", attributes_dictionary["GPF_AXCLR"], not_applicable=False)
        if int(attributes_dictionary["GPF_XTICK"]) < 1 or int(attributes_dictionary["GPF_XTICK"]) > 99:
            IntegerAttributeOutOfRange("GPF_XTICK", attributes_dictionary["GPF_XTICK"])
        if int(attributes_dictionary["GPF_YTICK"]) < 1 or int(attributes_dictionary["GPF_YTICK"]) > 99:
            IntegerAttributeOutOfRange("GPF_YTICK", attributes_dictionary["GPF_YTICK"])
        if int(attributes_dictionary["GPF_XGRID"]) < 1 or int(attributes_dictionary["GPF_XGRID"]) > 99:
            IntegerAttributeOutOfRange("GPF_XGRID", attributes_dictionary["GPF_XGRID"])
        if int(attributes_dictionary["GPF_YGRID"]) < 1 or int(attributes_dictionary["GPF_YGRID"]) > 99:
            IntegerAttributeOutOfRange("GPF_YGRID", attributes_dictionary["GPF_YGRID"])
        if (int(attributes_dictionary["GPF_UPUN"]) < 1 or int(attributes_dictionary["GPF_UPUN"]) > 99) and int(
                attributes_dictionary["GPF_UPUN"]) != 0:
            IntegerAttributeOutOfRange("GPF_UPUN", attributes_dictionary["GPF_UPUN"])

    elif class_type_str == "TXF":
        if attributes_dictionary["TXF_RAWFMT"] not in ['I', 'U', 'R']:
            InvalidAttribute("TXF_RAWFMT", attributes_dictionary["TXF_RAWFMT"], not_applicable=False)

    elif class_type_str == "CAF":
        if attributes_dictionary["CAF_ENGFMT"] not in ['I', 'U', 'R']:
            InvalidAttribute("CAF_ENGFMT", attributes_dictionary["CAF_ENGFMT"], not_applicable=False)
        if attributes_dictionary["CAF_RAWFMT"] not in ['I', 'U', 'R']:
            InvalidAttribute("CAF_RAWFMT", attributes_dictionary["CAF_RAWFMT"], not_applicable=False)
        if attributes_dictionary["CAF_RAWFMT"] == 'U':
            if attributes_dictionary["CAF_RADIX"] not in ['D', 'H', 'O'] and attributes_dictionary["CAF_RADIX"] != '':
                InvalidAttribute("CAF_RADIX", attributes_dictionary["CAF_RADIX"], not_applicable=False)
        if attributes_dictionary["CAF_RAWFMT"] != 'U':
            if attributes_dictionary["CAF_RADIX"] != '':
                InvalidAttribute("CAF_RADIX", attributes_dictionary["CAF_RADIX"], not_applicable=True)
        if attributes_dictionary["CAF_INTER"] not in ['P', 'F'] and attributes_dictionary["CAF_INTER"] != '':
            InvalidAttribute("CAF_INTER", attributes_dictionary["CAF_INTER"], not_applicable=False)

    elif class_type_str == "CAP":
        CAF_rows = session.query(schema.CAF).all()  # gets the CAF table

        # CAP_NUMBR
        CAF_attributes = []
        for CAF_object in CAF_rows:
            CAF_attributes.append(CAF_object.CAF_NUMBR)
        # print(CAF_object)
        if attributes_dictionary["CAP_NUMBR"] not in CAF_attributes:
            UnmatchingForeignKey('CAP_NUMBR', attributes_dictionary["CAP_NUMBR"], 'CAF_NUMBR', 'CAF_table')

    elif class_type_str == "PSV":
        PST_rows = session.query(schema.PST).all()  # gets the PST table

        # PSV_NAME
        PST_attributes = []
        for PST_object in PST_rows:
            PST_attributes.append(PST_object.PST_NAME)
        if attributes_dictionary["PSV_NAME"] not in PST_attributes:
            UnmatchingForeignKey('PSV_NAME', attributes_dictionary["PSV_NAME"], 'PST_NAME', 'PST_table')

    elif class_type_str == "TXP":
        TXF_rows = session.query(schema.TXF).all()  # gets the TXF table

        # TXP_NUMBR
        TXF_attributes = []
        for TXF_object in TXF_rows:
            TXF_attributes.append(TXF_object.TXF_NUMBR)
        if attributes_dictionary["TXP_NUMBR"] not in TXF_attributes:
            UnmatchingForeignKey('TXP_NUMBR', attributes_dictionary["TXP_NUMBR"], 'TXF_NUMBR', 'TXF_table')

    elif class_type_str == "CCF":
        TCP_rows = session.query(schema.TCP).all()  # gets the TCP table
        PSV_rows = session.query(schema.PSV).all()  # gets the PSV table

        # CCF_PKTID
        TCP_attributes = []
        for TCP_object in TCP_rows:
            TCP_attributes.append(TCP_object.TCP_ID)
        if attributes_dictionary["CCF_PKTID"] not in TCP_attributes:
            UnmatchingForeignKey('CCF_PKTID', attributes_dictionary["CCF_PKTID"], 'TCP_ID', 'TCP_table')
        # CCF_DEFSET
        PSV_attributes = []
        for PSV_object in PSV_rows:
            PSV_attributes.append(PSV_object.PSV_PVSID)
        if attributes_dictionary["CCF_DEFSET"] not in PSV_attributes and attributes_dictionary["CCF_DEFSET"] != '':
            UnmatchingForeignKey('CCF_DEFSET', attributes_dictionary["CCF_DEFSET"], 'PSV_PVSID', 'PSV_table')
        # other attributes
        if attributes_dictionary["CCF_CRITICAL"] not in ['Y', 'N'] and attributes_dictionary["CCF_CRITICAL"] != '':
            InvalidAttribute("CCF_CRITICAL", attributes_dictionary["CCF_CRITICAL"], not_applicable=False)
        if (int(attributes_dictionary["CCF_TYPE"]) < 0 or int(attributes_dictionary["CCF_TYPE"]) > 255) and \
                attributes_dictionary["CCF_TYPE"] != 0:
            IntegerAttributeOutOfRange("CCF_TYPE", attributes_dictionary["CCF_TYPE"])
        if (int(attributes_dictionary["CCF_STYPE"]) < 0 or int(attributes_dictionary["CCF_STYPE"]) > 255) and \
                attributes_dictionary["CCF_STYPE"] != 0:
            IntegerAttributeOutOfRange("CCF_STYPE", attributes_dictionary["CCF_STYPE"])
        if (int(attributes_dictionary["CCF_APID"]) < 0 or int(attributes_dictionary["CCF_APID"]) > 65535) and \
                attributes_dictionary["CCF_APID"] != 0:
            IntegerAttributeOutOfRange("CCF_APID", attributes_dictionary["CCF_APID"])
        if attributes_dictionary["CCF_PLAN"] not in ['A', 'F', 'S', 'N'] and attributes_dictionary["CCF_PLAN"] != '':
            InvalidAttribute("CCF_PLAN", attributes_dictionary["CCF_PLAN"], not_applicable=False)
        if attributes_dictionary["CCF_EXEC"] not in ['Y', 'N'] and attributes_dictionary["CCF_EXEC"] != '':
            InvalidAttribute("CCF_EXEC", attributes_dictionary["CCF_EXEC"], not_applicable=False)
        if attributes_dictionary["CCF_ILSCOPE"] not in ['G', 'L', 'S', 'B', 'F', 'T', 'N'] and attributes_dictionary[
            "CCF_ILSCOPE"] != '':
            InvalidAttribute("CCF_ILSCOPE", attributes_dictionary["CCF_ILSCOPE"], not_applicable=False)
        if attributes_dictionary["CCF_ILSTAGE"] not in ['R', 'U', 'O', 'A', 'C'] and attributes_dictionary[
            "CCF_ILSTAGE"] != '':
            InvalidAttribute("CCF_ILSTAGE", attributes_dictionary["CCF_ILSTAGE"], not_applicable=False)
        if (int(attributes_dictionary["CCF_SUBSYS"]) < 1 or int(attributes_dictionary["CCF_SUBSYS"]) > 255) and \
                attributes_dictionary["CCF_SUBSYS"] != 0:
            IntegerAttributeOutOfRange("CCF_SUBSYS", attributes_dictionary["CCF_SUBSYS"])
        if attributes_dictionary["CCF_HIPRI"] not in ['Y', 'N'] and attributes_dictionary["CCF_HIPRI"] != '':
            InvalidAttribute("CCF_HIPRI", attributes_dictionary["CCF_HIPRI"], not_applicable=False)
        if (int(attributes_dictionary["CCF_MAPID"]) < 0 or int(attributes_dictionary["CCF_MAPID"]) > 63) and \
                attributes_dictionary["CCF_MAPID"] != 0:
            IntegerAttributeOutOfRange("CCF_MAPID", attributes_dictionary["CCF_MAPID"])
        if (int(attributes_dictionary["CCF_RAPID"]) < 1 or int(attributes_dictionary["CCF_RAPID"]) > 65535) and \
                attributes_dictionary["CCF_RAPID"] != 0:
            IntegerAttributeOutOfRange("CCF_RAPID", attributes_dictionary["CCF_RAPID"])
        if (int(attributes_dictionary["CCF_ACK"]) < 0 or int(attributes_dictionary["CCF_ACK"]) > 15) and \
                attributes_dictionary["CCF_ACK"] != 0:
            IntegerAttributeOutOfRange("CCF_ACK", attributes_dictionary["CCF_ACK"])
        if attributes_dictionary["CCF_SUBSCHEDID"] == '':  # updates value to CCF_SUBSYS
            attributes_dictionary["CCF_SUBSCHEDID"] = attributes_dictionary["CCF_SUBSYS"]
            object_to_update.CCF_SUBSCHEDID = attributes_dictionary["CCF_SUBSYS"]
        elif (int(attributes_dictionary["CCF_SUBSCHEDID"]) < 1 or int(
                attributes_dictionary["CCF_SUBSCHEDID"]) > 65535) and int(attributes_dictionary["CCF_SUBSCHEDID"]) != 0:
            IntegerAttributeOutOfRange("CCF_SUBSCHEDID", attributes_dictionary["CCF_SUBSCHEDID"])

    elif class_type_str == "CSF":
        PSV_rows = session.query(schema.PSV).all()  # gets the PSV table

        # CSF_DEFSET
        PSV_attributes = []
        for PSV_object in PSV_rows:
            PSV_attributes.append(PSV_object.PSV_PVSID)
        if attributes_dictionary["CSF_DEFSET"] not in PSV_attributes and attributes_dictionary["CSF_DEFSET"] != '':
            UnmatchingForeignKey('CSF_DEFSET', attributes_dictionary["CSF_DEFSET"], 'PSV_PVSID', 'PSV_table')
        # other attributes
        if attributes_dictionary["CSF_IFTT"] not in ['Y', 'B', 'N'] and attributes_dictionary["CSF_IFTT"] != '':
            InvalidAttribute("CSF_IFTT", attributes_dictionary["CSF_IFTT"], not_applicable=False)
        if attributes_dictionary["CSF_CRITICAL"] not in ['Y', 'N'] and attributes_dictionary["CSF_CRITICAL"] != '':
            InvalidAttribute("CSF_CRITICAL", attributes_dictionary["CSF_CRITICAL"], not_applicable=False)
        if attributes_dictionary["CSF_PLAN"] not in ['A', 'F', 'S', 'N'] and attributes_dictionary["CSF_PLAN"] != '':
            InvalidAttribute("CSF_PLAN", attributes_dictionary["CSF_PLAN"], not_applicable=False)
        if attributes_dictionary["CSF_EXEC"] not in ['Y', 'N'] and attributes_dictionary["CSF_EXEC"] != '':
            InvalidAttribute("CSF_EXEC", attributes_dictionary["CSF_EXEC"], not_applicable=False)
        if (int(attributes_dictionary["CSF_SUBSYS"]) < 1 or int(attributes_dictionary["CSF_SUBSYS"]) > 255) and \
                attributes_dictionary["CSF_SUBSYS"] != 0:
            IntegerAttributeOutOfRange("CSF_SUBSYS", attributes_dictionary["CSF_SUBSYS"])
        if (int(attributes_dictionary["CSF_SUBSCHEDID"]) < 1 or int(
                attributes_dictionary["CSF_SUBSCHEDID"]) > 65535) and attributes_dictionary["CSF_SUBSCHEDID"] != 0:
            IntegerAttributeOutOfRange("CSF_SUBSCHEDID", attributes_dictionary["CSF_SUBSCHEDID"])

    elif class_type_str == "CSS":

        # CSS_ELEMID
        if attributes_dictionary["CSS_TYPE"] == 'C':
            CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
            CCF_attributes = []
            for CCF_object in CCF_rows:
                CCF_attributes.append(CCF_object.CCF_CNAME)
            if attributes_dictionary["CSS_ELEMID"] not in CCF_attributes and attributes_dictionary["CSS_ELEMID"] != '':
                UnmatchingForeignKey('CSS_ELEMID', attributes_dictionary["CSS_ELEMID"], 'CCF_CNAME', 'CCF_table')
        elif attributes_dictionary["CSS_TYPE"] == 'S':
            CSF_rows = session.query(schema.CSF).all()  # gets the CSF table
            CSF_attributes = []
            for CSF_object in CSF_rows:
                CSF_attributes.append(CSF_object.CSF_NAME)
            if attributes_dictionary["CSS_ELEMID"] not in CSF_attributes and attributes_dictionary["CSS_ELEMID"] != '':
                UnmatchingForeignKey('CSS_ELEMID', attributes_dictionary["CSS_ELEMID"], 'CSF_NAME', 'CSF_table')
        elif attributes_dictionary["CSS_TYPE"] in ['F', 'P']:
            CSP_rows = session.query(schema.CSP).all()  # gets the CSP table
            CSP_attributes = []
            for CSP_object in CSP_rows:
                CSP_attributes.append(CSP_object.CSP_FPNAME)
            if attributes_dictionary["CSS_ELEMID"] not in CSP_attributes and attributes_dictionary["CSS_ELEMID"] != '':
                UnmatchingForeignKey('CSS_ELEMID', attributes_dictionary["CSS_ELEMID"], 'CSP_FPNAME', 'CSP_table')
        elif attributes_dictionary["CSS_TYPE"] == 'T':
            if attributes_dictionary["CSS_ELEMID"] != '':
                print("CSS_ELEMID value changed to None")
                object_to_update.CSS_ELEMID = None

        # other attributes
        if attributes_dictionary["CSS_TYPE"] not in ['C', 'S', 'T', 'F', 'P']:
            InvalidAttribute("CSS_TYPE", attributes_dictionary["CSS_TYPE"], not_applicable=False)
        if attributes_dictionary["CSS_MANDISP"] not in ['Y', 'N'] and attributes_dictionary["CSS_MANDISP"] != '':
            InvalidAttribute("CSS_MANDISP", attributes_dictionary["CSS_MANDISP"], not_applicable=False)
        if attributes_dictionary["CSS_GROUP"] in ['M', 'E'] or attributes_dictionary["CSS_BLOCK"] in ['M', 'E']:
            print("CSS_MANDISP value changed to None")
            object_to_update.CSS_MANDISP = None
            print("CSS_RELTIME value changed to None")
            object_to_update.CSS_RELTIME = None
        if attributes_dictionary["CSS_RELTYPE"] not in ['R', 'A'] and attributes_dictionary["CSS_RELTYPE"] != '':
            InvalidAttribute("CSS_RELTYPE", attributes_dictionary["CSS_RELTYPE"], not_applicable=False)
        if attributes_dictionary["CSS_PREVREL"] not in ['R', 'A'] and attributes_dictionary["CSS_PREVREL"] != '':
            InvalidAttribute("CSS_PREVREL", attributes_dictionary["CSS_PREVREL"], not_applicable=False)
        if attributes_dictionary["CSS_GROUP"] not in ['S', 'M', 'E', '']:
            InvalidAttribute("CSS_GROUP", attributes_dictionary["CSS_GROUP"], not_applicable=False)
        if attributes_dictionary["CSS_BLOCK"] not in ['S', 'M', 'E'] and attributes_dictionary["CSS_BLOCK"] != '':
            InvalidAttribute("CSS_BLOCK", attributes_dictionary["CSS_BLOCK"], not_applicable=False)
        if attributes_dictionary["CSS_ILSCOPE"] not in ['G', 'L', 'S', 'B', 'F', 'T', 'N'] and attributes_dictionary[
            "CSS_ILSCOPE"] != '':
            InvalidAttribute("CSS_ILSCOPE", attributes_dictionary["CSS_ILSCOPE"], not_applicable=False)
        if (attributes_dictionary["CSS_BLOCK"] != '' or attributes_dictionary["CSS_GROUP"] != '') and \
                attributes_dictionary["CSS_ILSCOPE"] in ['G', 'L', ''] and (
                attributes_dictionary["CSS_BLOCK"] != 'E' or attributes_dictionary["CSS_GROUP"] != 'E'):
            InvalidAttribute("CSS_ILSCOPE", attributes_dictionary["CSS_ILSCOPE"], not_applicable=False)
        if attributes_dictionary["CSS_ILSTAGE"] not in ['R', 'U', 'O', 'A', 'C'] and attributes_dictionary[
            "CSS_ILSTAGE"] != '':
            InvalidAttribute("CSS_ILSTAGE", attributes_dictionary["CSS_ILSTAGE"], not_applicable=False)
        if attributes_dictionary["CSS_DYNPTV"] not in ['Y', 'N'] and attributes_dictionary["CSS_DYNPTV"] != '':
            InvalidAttribute("CSS_DYNPTV", attributes_dictionary["CSS_DYNPTV"], not_applicable=False)
        if attributes_dictionary["CSS_CEV"] not in ['Y', 'N'] and attributes_dictionary["CSS_CEV"] != '':
            InvalidAttribute("CSS_CEV", attributes_dictionary["CSS_CEV"], not_applicable=False)

    elif class_type_str == "PAF":
        if attributes_dictionary["PAF_RAWFMT"] not in ['I', 'U', 'R'] and attributes_dictionary["PAF_RAWFMT"] != '':
            InvalidAttribute("PAF_RAWFMT", attributes_dictionary["PAF_RAWFMT"], not_applicable=False)

    elif class_type_str == "PAS":
        PAF_rows = session.query(schema.PAF).all()  # gets the PAF table

        # PAS_NUMBR
        PAF_attributes = []
        for PAF_object in PAF_rows:
            PAF_attributes.append(PAF_object.PAF_NUMBR)
        if attributes_dictionary["PAS_NUMBR"] not in PAF_attributes:
            UnmatchingForeignKey('PAS_NUMBR', attributes_dictionary["PAS_NUMBR"], 'PAF_NUMBR', 'PAS_table')

    elif class_type_str == "DST":
        # DST_APID
        CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
        CCF_attributes = []
        for CCF_object in CCF_rows:
            CCF_attributes.append(CCF_object.CCF_APID)
        if attributes_dictionary["DST_APID"] not in CCF_attributes:
            UnmatchingForeignKey('DST_APID', attributes_dictionary["DST_APID"], 'CCF_APID', 'CCF_table')

        # DST_ROUTE
        if attributes_dictionary["DST_ROUTE"].count('.') not in [0, 1, 2]:
            InvalidAttribute("DST_ROUTE", attributes_dictionary["DST_ROUTE"], not_applicable=False)
        else:
            DST_ROUTE_params = attributes_dictionary["DST_ROUTE"].split('.')
            # first paramter
            if DST_ROUTE_params[0] not in ["NCTRS", "EGSE"]:
                InvalidAttribute("DST_ROUTE", attributes_dictionary["DST_ROUTE"], not_applicable=False)
            elif DST_ROUTE_params[0] == "NCTRS" and (
                    attributes_dictionary["DST_APID"] < 0 or attributes_dictionary["DST_APID"] > 2047):
                InvalidAttribute("DST_ROUTE", attributes_dictionary["DST_ROUTE"], not_applicable=False)
            # second parameter
            if attributes_dictionary["DST_ROUTE"].count('.') > 0 and DST_ROUTE_params[0] != "EGSE":
                InvalidAttribute("DST_ROUTE", attributes_dictionary["DST_ROUTE"], not_applicable=False)
            elif DST_ROUTE_params[1] not in ["SCOE", "TC"]:
                InvalidAttribute("DST_ROUTE", attributes_dictionary["DST_ROUTE"], not_applicable=False)

    elif class_type_str == "PID":
        if int(attributes_dictionary["PID_TYPE"]) < 0 or int(attributes_dictionary["PID_TYPE"]) > 255:
            IntegerAttributeOutOfRange("PID_TYPE", attributes_dictionary["PID_TYPE"])
        if int(attributes_dictionary["PID_STYPE"]) < 0 or int(attributes_dictionary["PID_STYPE"]) > 255:
            IntegerAttributeOutOfRange("PID_STYPE", attributes_dictionary["PID_STYPE"])
        if int(attributes_dictionary["PID_APID"]) < 0 or int(attributes_dictionary["PID_APID"]) > 65535:
            IntegerAttributeOutOfRange("PID_APID", attributes_dictionary["PID_APID"])
        if (int(attributes_dictionary["PID_PI1_VAL"]) < 0 or int(attributes_dictionary["PID_PI1_VAL"]) > (
                pow(2, 31) - 1)) and int(attributes_dictionary["PID_PI1_VAL"]) != 0:
            IntegerAttributeOutOfRange("PID_PI1_VAL", attributes_dictionary["PID_PI1_VAL"])
        if (int(attributes_dictionary["PID_PI2_VAL"]) < 0 or int(attributes_dictionary["PID_PI2_VAL"]) > (
                pow(2, 31) - 1)) and int(attributes_dictionary["PID_PI2_VAL"]) != 0:
            IntegerAttributeOutOfRange("PID_PI2_VAL", attributes_dictionary["PID_PI2_VAL"])
        if int(attributes_dictionary["PID_SPID"]) < 1 or int(attributes_dictionary["PID_SPID"]) > (pow(2, 31) - 1):
            IntegerAttributeOutOfRange("PID_SPID", attributes_dictionary["PID_SPID"])
        if (int(attributes_dictionary["PID_TPSD"]) < 1 or int(attributes_dictionary["PID_TPSD"]) > (
                pow(2, 31) - 1) or int(attributes_dictionary["PID_TPSD"]) == -1) and attributes_dictionary[
            "PID_TPSD"] != 0 and int(attributes_dictionary["PID_TPSD"]) != -1:
            IntegerAttributeOutOfRange("PID_TPSD", attributes_dictionary["PID_TPSD"])
        if int(attributes_dictionary["PID_DFHSIZE"]) < 0 or int(attributes_dictionary["PID_DFHSIZE"]) > 99:
            IntegerAttributeOutOfRange("PID_DFHSIZE", attributes_dictionary["PID_DFHSIZE"])
        if attributes_dictionary["PID_TIME"] not in ['Y', 'N'] and attributes_dictionary["PID_TIME"] != '':
            InvalidAttribute("PID_TIME", attributes_dictionary["PID_TIME"], not_applicable=False)
        if attributes_dictionary["PID_VALID"] not in ['Y', 'N'] and attributes_dictionary["PID_VALID"] != '':
            InvalidAttribute("PID_VALID", attributes_dictionary["PID_INTER"], not_applicable=False)
        if int(attributes_dictionary["PID_CHECK"]) not in [0, 1] and int(attributes_dictionary["PID_CHECK"]) != 0:
            InvalidAttribute("PID_CHECK", attributes_dictionary["PID_CHECK"], not_applicable=False)
        if attributes_dictionary["PID_EVENT"] not in ['N', 'I', 'W', 'A'] and attributes_dictionary["PID_EVENT"] != '':
            InvalidAttribute("PID_EVENT", attributes_dictionary["PID_EVENT"], not_applicable=False)

        # PID_EVID
        if attributes_dictionary["PID_EVID"] != '':
            try:  # supposing nnnn is entered
                evid = int(attributes_dictionary["PID_EVID"])
            except ValueError:  # supposing TPKT_OBE::nnnn is entered
                pass
            else:
                attributes_dictionary["PID_EVID"] = "TPKT_OBE::" + str(evid)
                object_to_update.PID_EVID = "TPKT_OBE::" + str(evid)

    elif class_type_str == "CVS":
        PID_rows = session.query(schema.PID).all()  # gets the PID table

        # CVS_SPID
        if attributes_dictionary["CVS_SOURCE"] == 'V' and attributes_dictionary["CVS_SPID"] != '':
            PID_attributes = []
            for PID_object in PID_rows:
                PID_attributes.append(PID_object.PID_SPID)
            if attributes_dictionary["CVS_SPID"] not in PID_attributes:
                UnmatchingForeignKey('CVS_SPID', attributes_dictionary["CVS_SPID"], 'PID_SPID', 'PID_table')
        elif attributes_dictionary["CVS_SOURCE"] == 'R' and attributes_dictionary["CVS_SPID"] != '':
            InvalidAttribute("CVS_SPID", attributes_dictionary["CVS_SPID"], not_applicable=True)

        # Other attributes
        if int(attributes_dictionary["CVS_ID"]) < 0 or int(attributes_dictionary["CVS_ID"]) > 32767:
            IntegerAttributeOutOfRange("CVS_ID", attributes_dictionary["CVS_ID"])
        if attributes_dictionary["CVS_TYPE"] not in ['A', 'S', 'C', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            InvalidAttribute("CVS_TYPE", attributes_dictionary["CVS_TYPE"], not_applicable=False)
        if attributes_dictionary["CVS_SOURCE"] not in ['V', 'R']:
            InvalidAttribute("CVS_SOURCE", attributes_dictionary["CVS_SOURCE"], not_applicable=False)
        if attributes_dictionary["CVS_SOURCE"] == 'R' and attributes_dictionary["CVS_TYPE"] != '0':
            InvalidAttribute("CVS_SOURCE", attributes_dictionary["CVS_SOURCE"], not_applicable=False)
        if int(attributes_dictionary["CVS_START"]) < 0:
            IntegerAttributeOutOfRange("CVS_START", attributes_dictionary["CVS_START"])
        if int(attributes_dictionary["CVS_INTERVAL"]) < 0:
            IntegerAttributeOutOfRange("CVS_INTERVAL", attributes_dictionary["CVS_INTERVAL"])

            # second constraint is redundant but it is written for the sake of homogeneity
        if int(attributes_dictionary["CVS_INTERVAL"]) < -1 and int(attributes_dictionary[
                                                                       "CVS_INTERVAL"]) != 0:
            IntegerAttributeOutOfRange("CVS_INTERVAL", attributes_dictionary["CVS_INTERVAL"])

    elif class_type_str == "VPD":
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table

        # VPD_NAME
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["VPD_NAME"] not in PCF_attributes:
            UnmatchingForeignKey('VPD_NAME', attributes_dictionary["VPD_NAME"], 'PCF_NAME', 'PCF_table')
        # other attributes
        if int(attributes_dictionary["VPD_TPSD"]) < 0:
            IntegerAttributeOutOfRange("VPD_TPSD", attributes_dictionary["VPD_TPSD"])
        if int(attributes_dictionary["VPD_POS"]) < 0:
            IntegerAttributeOutOfRange("VPD_POS", attributes_dictionary["VPD_POS"])
        if int(attributes_dictionary["VPD_POS"]) < -1 and int(attributes_dictionary[
                                                                  "VPD_POS"]) != 0:  # second constraint is redundant but it is written for the sake of homogeinity
            IntegerAttributeOutOfRange("VPD_POS", attributes_dictionary["VPD_POS"])
        if attributes_dictionary["VPD_CHOICE"] not in ['Y', 'N'] and attributes_dictionary["VPD_CHOICE"] != '':
            InvalidAttribute("VPD_CHOICE", attributes_dictionary["VPD_CHOICE"], not_applicable=False)
        if attributes_dictionary["VPD_PIDREF"] not in ['Y', 'N'] and attributes_dictionary["VPD_PIDREF"] != '':
            InvalidAttribute("VPD_PIDREF", attributes_dictionary["VPD_PIDREF"], not_applicable=False)
        if int(attributes_dictionary["VPD_WIDTH"]) < 0:
            IntegerAttributeOutOfRange("VPD_WIDTH", attributes_dictionary["VPD_WIDTH"])
        if attributes_dictionary["VPD_JUSTIFY"] not in ['L', 'R', 'C'] and attributes_dictionary["VPD_JUSTIFY"] != '':
            InvalidAttribute("VPD_JUSTIFY", attributes_dictionary["VPD_JUSTIFY"], not_applicable=False)
        if attributes_dictionary["VPD_NEWLINE"] not in ['Y', 'N'] and attributes_dictionary["VPD_NEWLINE"] != '':
            InvalidAttribute("VPD_NEWLINE", attributes_dictionary["VPD_NEWLINE"], not_applicable=False)
        if int(attributes_dictionary["VPD_DCHAR"]) not in [0, 1, 2] and int(attributes_dictionary[
                                                                                "VPD_DCHAR"]) != 0:  # second constraint is redundant but it is written for the sake of homogeinity
            IntegerAttributeOutOfRange("VPD_DCHAR", attributes_dictionary["VPD_DCHAR"])
        if attributes_dictionary["VPD_FORM"] not in ['B', 'O', 'D', 'H', 'N'] and attributes_dictionary[
            "VPD_FORM"] != '':
            InvalidAttribute("VPD_FORM", attributes_dictionary["VPD_FORM"], not_applicable=False)
        if (int(attributes_dictionary["VPD_OFFSET"]) < -32768 or int(
                attributes_dictionary["VPD_OFFSET"]) > 32767) and int(attributes_dictionary[
                                                                          "VPD_OFFSET"]) != 0:  # second constraint is redundant but it is written for the sake of homogeinity
            IntegerAttributeOutOfRange("VPD_OFFSET", attributes_dictionary["VPD_OFFSET"])

    elif class_type_str == "PCF":
        # PCF_CURTX
        if attributes_dictionary["PCF_CURTX"] != '':
            if attributes_dictionary["PCF_CATEG"] == 'S':
                TXF_rows = session.query(schema.TXF).all()  # gets the TXF table
                TXF_attributes = []
                for TXF_object in TXF_rows:
                    TXF_attributes.append(TXF_object.TXF_NUMBR)
                if attributes_dictionary["PCF_CURTX"] not in TXF_attributes:
                    UnmatchingForeignKey('PCF_CURTX', attributes_dictionary["PCF_CURTX"], 'TXF_NUMBR', 'TXF_table')
            elif attributes_dictionary["PCF_CATEG"] == 'N':
                CAF_rows = session.query(schema.CAF).all()  # gets the CAF table
                CAF_attributes = []
                for CAF_object in CAF_rows:
                    CAF_attributes.append(CAF_object.CAF_NUMBR)
                MCF_rows = session.query(schema.MCF).all()  # gets the MCF table
                MCF_attributes = []
                for MCF_object in MCF_rows:
                    MCF_attributes.append(MCF_object.MCF_IDENT)
                LGF_rows = session.query(schema.LGF).all()  # gets the LGF table
                LGF_attributes = []
                for LGF_object in LGF_rows:
                    LGF_attributes.append(LGF_object.LGF_IDENT)
                if attributes_dictionary["PCF_CURTX"] not in CAF_attributes or attributes_dictionary[
                    "PCF_CURTX"] not in MCF_attributes or attributes_dictionary["PCF_CURTX"] not in LGF_attributes:
                    UnmatchingForeignKey('PCF_CURTX', attributes_dictionary["PCF_CURTX"],
                                         'CAF_NUMBR or MCF_IDENT or LGF_IDENT', 'CAF_table/ MCF_table/ LGF_table')
            elif attributes_dictionary["PCF_CATEG"] == 'T' or int(attributes_dictionary["PCF_PTC"]) in [7, 8, 9,
                                                                                                        10]:  # field must be left NULL:
                print("PCF_CURTX changed to NULL")
                object_to_update.PCF_CURTX = None
        if attributes_dictionary["PCF_CURTX"] == '' and attributes_dictionary[
            "PCF_CATEG"] == 'S':  # field cannot be left NULL
            InvalidAttribute("PCF_CURTX", attributes_dictionary["PCF_CURTX"], not_applicable=False)
        # Other attributes
        if attributes_dictionary["PCF_NAME"][0:3] == "VAR" or attributes_dictionary["PCF_NAME"][0:4] == "GVAR" or \
                attributes_dictionary["PCF_NAME"][0] == "$":
            InvalidAttribute("PCF_NAME", attributes_dictionary["PCF_NAME"], not_applicable=False)
        if (int(attributes_dictionary["PCF_PID"]) < 0 or int(attributes_dictionary["PCF_PID"]) > (
                pow(2, 31) - 1)) and int(attributes_dictionary["PCF_PID"]) != 0:
            IntegerAttributeOutOfRange("PCF_PID", attributes_dictionary["PCF_PID"])
        if int(attributes_dictionary["PCF_PTC"]) < 1 or int(attributes_dictionary["PCF_PTC"]) > 13:
            IntegerAttributeOutOfRange("PCF_PTC", attributes_dictionary["PCF_PTC"])
        if attributes_dictionary["PCF_NATUR"] == 'S' and int(attributes_dictionary["PCF_PTC"]) != 13:
            print("PCF_NATUR changed to 13")
            object_to_update.PCF_NATUR = 13
        if checkAppendixA(int(attributes_dictionary["PCF_PTC"]), int(attributes_dictionary["PCF_PFC"])) == False:
            IntegerAttributeOutOfRange("PCF_PFC", attributes_dictionary["PCF_PFC"])
        if attributes_dictionary["PCF_CATEG"] not in ['N', 'S', 'T']:
            InvalidAttribute("PCF_CATEG", attributes_dictionary["PCF_CATEG"], not_applicable=False)
        if int(attributes_dictionary["PCF_PTC"]) in [6, 7, 9, 10] and attributes_dictionary["PCF_CATEG"] != 'N':
            print("PCF_CATEG changed to 'N'")
            object_to_update.PCF_CATEG = 'N'
        if int(attributes_dictionary["PCF_PTC"]) == 8 and attributes_dictionary["PCF_CATEG"] != 'T':
            print("PCF_CATEG changed to 'T'")
            object_to_update.PCF_CATEG = 'T'
        if attributes_dictionary["PCF_NATUR"] not in ['R', 'D', 'P', 'H', 'S', 'C']:
            InvalidAttribute("PCF_NATUR", attributes_dictionary["PCF_NATUR"], not_applicable=False)
        if attributes_dictionary["PCF_INTER"] not in ['P', 'F'] and attributes_dictionary["PCF_INTER"] != '':
            InvalidAttribute("PCF_INTER", attributes_dictionary["PCF_INTER"], not_applicable=False)
        if attributes_dictionary["PCF_USCON"] not in ['N', 'Y'] and attributes_dictionary[
            "PCF_USCON"] != '':  # field must be corrected later (when OCP is available)
            InvalidAttribute("PCF_USCON", attributes_dictionary["PCF_USCON"], not_applicable=False)
        if attributes_dictionary["PCF_NATUR"] != 'C' and attributes_dictionary["PCF_PARVAL"] != '':
            InvalidAttribute("PCF_PARVAL", attributes_dictionary["PCF_PARVAL"], not_applicable=True)
        elif attributes_dictionary["PCF_NATUR"] == 'C' and attributes_dictionary[
            "PCF_PARVAL"] == '':  # field cannot be left NULL
            InvalidAttribute("PCF_PARVAL", attributes_dictionary["PCF_PARVAL"], not_applicable=False)
        if attributes_dictionary["PCF_SPTYPE"] not in ['E', 'R'] and attributes_dictionary["PCF_SPTYPE"] != '':
            InvalidAttribute("PCF_SPTYPE", attributes_dictionary["PCF_SPTYPE"], not_applicable=False)
        if attributes_dictionary["PCF_CORR"] not in ['Y', 'N'] and attributes_dictionary["PCF_CORR"] != '':
            InvalidAttribute("PCF_CORR", attributes_dictionary["PCF_CORR"], not_applicable=False)
        if int(attributes_dictionary["PCF_PTC"]) == 10 and attributes_dictionary["PCF_CORR"] != 'N':
            print("PCF_CORR changed to 'N'")
            object_to_update.PCF_CORR = 'N'
        if attributes_dictionary["PCF_DARC"] not in ['0', '1'] and attributes_dictionary["PCF_DARC"] != '':
            InvalidAttribute("PCF_DARC", attributes_dictionary["PCF_DARC"], not_applicable=False)
        if attributes_dictionary["PCF_ENDIAN"] not in ['B', 'L'] and attributes_dictionary["PCF_ENDIAN"] != '':
            InvalidAttribute("PCF_ENDIAN", attributes_dictionary["PCF_ENDIAN"], not_applicable=False)

    elif class_type_str == "OCF":
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table

        # OCF_NAME
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["OCF_NAME"] not in PCF_attributes:
            UnmatchingForeignKey('OCF_NAME', attributes_dictionary["OCF_NAME"], 'PCF_NAME', 'PCF_table')
        # other attributes
        if int(attributes_dictionary["OCF_NBOOL"]) < 1 or int(attributes_dictionary["OCF_NBOOL"]) > 16:
            IntegerAttributeOutOfRange("OCF_NBOOL", attributes_dictionary["OCF_NBOOL"])
        if attributes_dictionary["OCF_INTER"] not in ['U', 'C']:
            InvalidAttribute("OCF_INTER", attributes_dictionary["OCF_INTER"], not_applicable=False)
        if attributes_dictionary["OCF_CODIN"] not in ['R', 'A', 'I']:
            InvalidAttribute("OCF_CODIN", attributes_dictionary["OCF_CODIN"], not_applicable=False)

        # OCF_CODIN constraints
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["OCF_NAME"]).first()
        CAF_object = session.query(schema.CAF).filter_by(PCF_NAME=attributes_dictionary["OCF_NAME"]).first()  # ¿?
        if PCF_object is None:
            UnmatchingForeignKey("OCF_NAME", attributes_dictionary["OCF_NAME"], "PCF_NAME", "PCF_table")
        else:
            if attributes_dictionary["OCF_CODIN"] == 'R':
                if attributes_dictionary["OCF_INTER"] == 'U' and int(PCF_object.PCF_PTC) == 5:
                    pass
                elif attributes_dictionary["OCF_INTER"] == 'C':
                    pass
                elif PCF_object.PCF_CATEG == 'N':
                    pass
                else:
                    InvalidAttribute("OCF_CODIN", attributes_dictionary["OCF_CODIN"], not_applicable=False)
            elif attributes_dictionary["OCF_CODIN"] == 'A':
                if PCF_object.PCF_CATEG == 'S' and attributes_dictionary["OCF_INTER"] == 'C':
                    pass
                else:
                    InvalidAttribute("OCF_CODIN", attributes_dictionary["OCF_CODIN"], not_applicable=False)
            elif attributes_dictionary["OCF_CODIN"] == 'I':
                if attributes_dictionary["OCF_INTER"] == 'U' and int(PCF_object.PCF_PTC) < 5:
                    pass
                elif attributes_dictionary["OCF_INTER"] == 'C' and PCF_object.PCF_CATEG == 'N':
                    pass
                else:
                    attributes_dictionary["OCF_INTER"] == 'U'

    elif class_type_str == "OCP":
        # OCP_NAME
        OCF_rows = session.query(schema.OCF).all()  # gets the OCF table
        OCF_attributes = []
        for OCF_object in OCF_rows:
            OCF_attributes.append(OCF_object.OCF_NAME)
        if attributes_dictionary["OCP_NAME"] not in OCF_attributes:
            UnmatchingForeignKey('OCP_NAME', attributes_dictionary["OCP_NAME"], 'OCF_NAME', 'OCF_table')
        # OCP_TYPE
        if attributes_dictionary["OCP_TYPE"] not in ['S', 'H', 'D', 'C', 'E']:
            InvalidAttribute("OCP_TYPE", attributes_dictionary["OCP_TYPE"], not_applicable=False)
        if attributes_dictionary["OCP_TYPE"] == 'C':
            PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["OCP_NAME"]).first()
            if PCF_object is None:
                UnmatchingForeignKey("OCP_NAME", attributes_dictionary["OCP_NAME"], "PCF_NAME", "PCF_table")
            else:
                if PCF_object.PCF_USCON != 'Y':  # updates PCF
                    print("Row with PCF_NAME: %s had field PCF_USCON changed to 'Y'")
                    session.delete(PCF_object)
                    session.commit()
                    session.make_transient(PCF_object)
                    PCF_object.PCF_USCON = 'Y'
                    session.add(PCF_object)
        # OCP_LVALU
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["OCP_NAME"]).first()
        if PCF_object is None:
            UnmatchingForeignKey("OCP_NAME", attributes_dictionary["OCP_NAME"], "PCF_NAME", "PCF_table")
        else:
            if PCF_object.PCF_CATEG == 'N' and attributes_dictionary["OCP_TYPE"] in ['S', 'H', 'E'] and \
                    attributes_dictionary["OCP_LVALU"] == '':
                InvalidAttribute("OCP_LVALU", attributes_dictionary["OCP_LVALU"], not_applicable=False)
            if PCF_object.PCF_CATEG == 'S' and attributes_dictionary["OCP_TYPE"] in ['S', 'H'] and \
                    attributes_dictionary["OCP_LVALU"] == '':
                InvalidAttribute("OCP_LVALU", attributes_dictionary["OCP_LVALU"], not_applicable=False)
        # OCP_HVALU
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["OCP_NAME"]).first()
        if PCF_object is None:
            UnmatchingForeignKey("OCP_NAME", attributes_dictionary["OCP_NAME"], "PCF_NAME", "PCF_table")
        else:
            if PCF_object.PCF_CATEG == 'N' and attributes_dictionary["OCP_TYPE"] in ['S', 'H', 'E'] and \
                    attributes_dictionary["OCP_LVALU"] == '':
                InvalidAttribute("OCP_LVALU", attributes_dictionary["OCP_LVALU"], not_applicable=False)
        # other fields
        if attributes_dictionary["OCP_TYPE"] == 'C' and attributes_dictionary["OCP_RLCHK"] != '':
            InvalidAttribute("OCP_RLCHK", attributes_dictionary["OCP_RLCHK"], not_applicable=True)
        if attributes_dictionary["OCP_TYPE"] == 'C' and attributes_dictionary["OCP_VALPAR"] != '':
            InvalidAttribute("OCP_VALPAR", attributes_dictionary["OCP_VALPAR"], not_applicable=True)

    elif class_type_str == "GRP":
        if attributes_dictionary["GRP_GTYPE"] not in ['PA', 'PK']:
            InvalidAttribute("GRP_GTYPE", attributes_dictionary["GRP_GTYPE"], not_applicable=False)

    elif class_type_str == "GRPA":
        # GRPA_GNAME
        GRP_rows = session.query(schema.GRP).all()  # gets the GRP table
        GRP_attributes = []
        for GRP_object in GRP_rows:
            GRP_attributes.append(GRP_object.GRP_NAME)
        if attributes_dictionary["GRPA_GNAME"] not in GRP_attributes:
            UnmatchingForeignKey('GRPA_GNAME', attributes_dictionary["GRPA_GNAME"], 'GRP_NAME', 'GRP_table')
        GRP_object = session.query(schema.GRP).filter_by(GRP_NAME=attributes_dictionary["GRPA_GNAME"]).first()
        if GRP_object is None:
            UnmatchingForeignKey("GRPA_GNAME", attributes_dictionary["GRPA_GNAME"], "GRP_NAME", "GRP_table")
        else:
            if GRP_object.GRP_GTYPE != 'PA':
                UnmatchingForeignKey('GRPA_GNAME', attributes_dictionary["GRPA_GNAME"], 'GRP_GTYPE', 'GRP_table')

        # GRPA_PANAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["GRPA_PANAME"] not in PCF_attributes:
            UnmatchingForeignKey('GRPA_PANAME', attributes_dictionary["GRPA_PANAME"], 'PCF_NAME', 'PCF_table')

    elif class_type_str == "GRPK":
        # GRPK_GNAME
        GRP_rows = session.query(schema.GRP).all()  # gets the GRP table
        GRP_attributes = []
        for GRP_object in GRP_rows:
            GRP_attributes.append(GRP_object.GRP_NAME)
        if attributes_dictionary["GRPK_GNAME"] not in GRP_attributes:
            UnmatchingForeignKey('GRPK_GNAME', attributes_dictionary["GRPK_GNAME"], 'GRP_NAME', 'GRP_table')
        GRP_object = session.query(schema.GRP).filter_by(GRP_NAME=attributes_dictionary["GRPK_GNAME"]).first()
        if GRP_object is None:
            UnmatchingForeignKey("GRPK_GNAME", attributes_dictionary["GRPK_GNAME"], "GRP_NAME", "GRP_table")
        else:
            if GRP_object.GRP_GTYPE != 'PK':
                UnmatchingForeignKey('GRPK_GNAME', attributes_dictionary["GRPK_GNAME"], 'GRP_GTYPE', 'GRP_table')

        # GRPK_PKSPID
        PID_rows = session.query(schema.PID).all()  # gets the PID table
        PID_attributes = []
        for PID_object in PID_rows:
            PID_attributes.append(PID_object.PID_SPID)
        if attributes_dictionary["GRPK_PKSPID"] not in PID_attributes:
            UnmatchingForeignKey('GRPK_PKSPID', attributes_dictionary["GRPK_PKSPID"], 'PID_SPID', 'PID_table')

    elif class_type_str == "PLF":
        # PLF_NAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["PLF_NAME"] not in PCF_attributes:
            UnmatchingForeignKey('PLF_NAME', attributes_dictionary["PLF_NAME"], 'PCF_NAME', 'PCF_table')

        # PLF_SPID
        PID_rows = session.query(schema.PID).all()  # gets the PID table
        PID_attributes = []
        for PID_object in PID_rows:
            PID_attributes.append(PID_object.PID_SPID)
        if attributes_dictionary["PLF_SPID"] not in PID_attributes:
            UnmatchingForeignKey('PLF_SPID', attributes_dictionary["PLF_SPID"], 'PID_SPID', 'PID_table')
        # other attributes
        if int(attributes_dictionary["PLF_OFFBY"]) < 0:
            IntegerAttributeOutOfRange("PLF_OFFBY", attributes_dictionary["PLF_OFFBY"])
        if int(attributes_dictionary["PLF_OFFBI"]) < 0 or int(attributes_dictionary["PLF_OFFBI"]) > 7:
            IntegerAttributeOutOfRange("PLF_OFFBI", attributes_dictionary["PLF_OFFBI"])
        if (int(attributes_dictionary["PLF_NBOCC"]) < 1 or int(attributes_dictionary["PLF_NBOCC"]) > 9999) and int(
                attributes_dictionary["PLF_NBOCC"]) != 0:
            IntegerAttributeOutOfRange("PLF_NBOCC", attributes_dictionary["PLF_NBOCC"])
        if (int(attributes_dictionary["PLF_LGOCC"]) < 0 or int(attributes_dictionary["PLF_LGOCC"]) > 32767) and int(
                attributes_dictionary["PLF_LGOCC"]) != 0:
            IntegerAttributeOutOfRange("PLF_LGOCC", attributes_dictionary["PLF_LGOCC"])
        if (int(attributes_dictionary["PLF_TIME"]) < -4080000 or int(
                attributes_dictionary["PLF_TIME"]) > 4080000) and int(attributes_dictionary["PLF_TIME"]) != 0:
            IntegerAttributeOutOfRange("PLF_TIME", attributes_dictionary["PLF_TIME"])
        if (int(attributes_dictionary["PLF_TDOCC"]) < 1 or int(attributes_dictionary["PLF_TDOCC"]) > 4080000) and int(
                attributes_dictionary["PLF_TDOCC"]) != 0:
            IntegerAttributeOutOfRange("PLF_TDOCC", attributes_dictionary["PLF_TDOCC"])

    elif class_type_str == "TPCF":
        # TPCF_SPID
        PID_rows = session.query(schema.PID).all()  # gets the PID table
        PID_attributes = []
        for PID_object in PID_rows:
            PID_attributes.append(PID_object.PID_SPID)
        if attributes_dictionary["TPCF_SPID"] not in PID_attributes:
            UnmatchingForeignKey('TPCF_SPID', attributes_dictionary["TPCF_SPID"], 'PID_SPID', 'PID_table')

    elif class_type_str == "SPF":
        if int(attributes_dictionary["SPF_NPAR"]) < 1 or int(attributes_dictionary["SPF_NPAR"]) > 5:
            IntegerAttributeOutOfRange("SPF_NPAR", attributes_dictionary["SPF_NPAR"])
        if int(attributes_dictionary["SPF_UPUN"]) < 1 or int(attributes_dictionary["SPF_UPUN"]) > 99:
            IntegerAttributeOutOfRange("SPF_UPUN", attributes_dictionary["SPF_UPUN"])

    elif class_type_str == "SPC":
        # SPC_NUMBE
        SPF_rows = session.query(schema.SPF).all()  # gets the SPF table
        SPF_attributes = []
        for SPF_object in SPF_rows:
            SPF_attributes.append(SPF_object.SPF_NUMBE)
        if attributes_dictionary["SPC_NUMBE"] not in SPF_attributes:
            UnmatchingForeignKey('SPC_NUMBE', attributes_dictionary["SPC_NUMBE"], 'SPF_NUMBE', 'SPF_table')

        # SPC_NAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["SPC_NAME"] not in PCF_attributes:
            UnmatchingForeignKey('SPC_NAME', attributes_dictionary["SPC_NAME"], 'PCF_NAME', 'PCF_table')
        # other attributes
        if attributes_dictionary["SPC_UPDT"] not in [' ', '', 'N']:  # empty string is actually a valid value
            InvalidAttribute("SPC_UPDT", attributes_dictionary["SPC_UPDT"], not_applicable=False)
        if attributes_dictionary["SPC_MODE"] not in [' ', '', 'N']:  # empty string is actually a valid value
            InvalidAttribute("SPC_MODE", attributes_dictionary["SPC_MODE"], not_applicable=False)
        if attributes_dictionary["SPC_FORM"] not in ['B', 'O', 'D', 'H', 'N'] and attributes_dictionary[
            "SPC_FORM"] != '':
            InvalidAttribute("SPC_FORM", attributes_dictionary["SPC_FORM"], not_applicable=False)
        if attributes_dictionary["SPC_BACK"] not in ['0', '1', '2', '3', '4', '5', '6', '7'] and attributes_dictionary[
            "SPC_FORM"] != '':
            InvalidAttribute("SPC_BACK", attributes_dictionary["SPC_BACK"], not_applicable=False)
        if attributes_dictionary["SPC_FORE"] not in ['0', '1', '2', '3', '4', '5', '6', '7']:
            InvalidAttribute("SPC_FORE", attributes_dictionary["SPC_FORE"], not_applicable=False)

    elif class_type_str == "PCPC":
        if attributes_dictionary["PCPC_CODE"] not in ['I', 'U'] and attributes_dictionary["PCPC_CODE"] != '':
            InvalidAttribute("PCPC_CODE", attributes_dictionary["PCPC_CODE"], not_applicable=False)

    elif class_type_str == "PCDF":
        # PCDF_TCNAME
        TCP_rows = session.query(schema.TCP).all()  # gets the TCP table
        TCP_attributes = []
        for TCP_object in TCP_rows:
            TCP_attributes.append(TCP_object.TCP_ID)
        if attributes_dictionary["PCDF_TCNAME"] not in TCP_attributes:
            UnmatchingForeignKey('PCDF_TCNAME', attributes_dictionary["PCDF_TCNAME"], 'TCP_ID', 'TCP_table')

        # other attributes
        if attributes_dictionary["PCDF_TYPE"] not in ['F', 'A', 'T', 'S', 'K', 'P']:
            InvalidAttribute("PCDF_TYPE", attributes_dictionary["PCDF_TYPE"], not_applicable=False)
        if int(attributes_dictionary["PCDF_LEN"]) < 0:
            IntegerAttributeOutOfRange("PCDF_LEN", attributes_dictionary["PCDF_LEN"])
        if int(attributes_dictionary["PCDF_BIT"]) < 0:
            IntegerAttributeOutOfRange("PCDF_BIT", attributes_dictionary["PCDF_BIT"])
        if attributes_dictionary["PCDF_TYPE"] not in ['A', 'T', 'S', 'K', 'P'] and attributes_dictionary[
            "PCDF_TYPE"] != '':
            InvalidAttribute("PCDF_PNAME", attributes_dictionary["PCDF_PNAME"], not_applicable=True)
        elif attributes_dictionary["PCDF_TYPE"] == 'F' and attributes_dictionary["PCDF_PNAME"] != '':
            print("PCDF_PNAME changed to NULL")
            object_to_update.PCDF_PNAME = None
        if attributes_dictionary["PCDF_RADIX"] not in ['D', 'H', 'O'] and attributes_dictionary["PCDF_RADIX"] != '':
            InvalidAttribute("PCDF_RADIX", attributes_dictionary["PCDF_RADIX"], not_applicable=False)

    elif class_type_str == "PSM":
        # PSM_NAME
        CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
        CCF_attributes = []
        CSF_rows = session.query(schema.CSF).all()  # gets the CSF table
        CSF_attributes = []
        for CCF_object in CCF_rows:
            CCF_attributes.append(CCF_object.CCF_CNAME)
        for CSF_object in CSF_rows:
            CSF_attributes.append(CSF_object.CSF_NAME)
        if attributes_dictionary["PSM_NAME"] not in CCF_attributes or attributes_dictionary[
            "PSM_NAME"] not in CSF_attributes:
            UnmatchingForeignKey('PSM_NAME', attributes_dictionary["PSM_NAME"], 'CCF_CNAME or CSF_NAME',
                                 'CCF_table and CSF_table')
        # PSM_PARSET
        PST_rows = session.query(schema.PST).all()  # gets the PST table
        PST_attributes = []
        for PST_object in PST_rows:
            PST_attributes.append(PST_object.PST_NAME)
        if attributes_dictionary["PSM_PARSET"] not in PST_attributes:
            UnmatchingForeignKey('PSM_PARSET', attributes_dictionary["PSM_PARSET"], 'PST_NAME', 'PST_table')

        # other attributes
        if attributes_dictionary["PSM_TYPE"] not in ['C', 'S']:
            InvalidAttribute("PSM_TYPE", attributes_dictionary["PSM_TYPE"], not_applicable=False)

    elif class_type_str == "PTV":
        # PTV_CNAME
        CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
        CCF_attributes = []
        for CCF_object in CCF_rows:
            CCF_attributes.append(CCF_object.CCF_CNAME)
        if attributes_dictionary["PTV_CNAME"] not in CCF_attributes:
            UnmatchingForeignKey('PTV_CNAME', attributes_dictionary["PTV_CNAME"], 'CCF_CNAME', 'CCF_table')

        # PTV_PARNAM
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["PTV_PARNAM"] not in PCF_attributes:
            UnmatchingForeignKey('PTV_PARNAM', attributes_dictionary["PTV_PARNAM"], 'PCF_NAME', 'PCF_table')

        # PTV_INTER
        if attributes_dictionary["PTV_INTER"] not in ['E', 'R'] and attributes_dictionary["PTV_INTER"] != '':
            InvalidAttribute("PTV_INTER", attributes_dictionary["PTV_INTER"], not_applicable=False)
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["PTV_PARNAM"]).first()
        if PCF_object is None:
            UnmatchingForeignKey("PTV_PARNAM", attributes_dictionary["PTV_PARNAM"], "PCF_NAME", "PCF_table")
        else:
            if attributes_dictionary["PTV_INTER"] == 'E' and PCF_object.PCF_CURTX is None:
                InvalidAttribute("PTV_INTER", attributes_dictionary["PTV_INTER"], not_applicable=False)

    elif class_type_str == "GPC":
        # GPC_NUMBE
        GPF_rows = session.query(schema.GPF).all()  # gets the GPF table
        GPF_attributes = []
        for GPF_object in GPF_rows:
            GPF_attributes.append(GPF_object.GPF_NUMBE)
        if attributes_dictionary["GPC_NUMBE"] not in GPF_attributes:
            UnmatchingForeignKey('GPC_NUMBE', attributes_dictionary["GPC_NUMBE"], 'GPF_NUMBE', 'GPF_table')

        # GPC_WHERE
        GPF_object = session.query(schema.GPF).filter_by(GPF_NUMBE=attributes_dictionary["GPC_NUMBE"]).first()
        if GPF_object is None:
            UnmatchingForeignKey("GPC_NUMBE", attributes_dictionary["GPC_NUMBE"], "GPF_NUMBE", "GPF_table")
        else:
            if GPF_object.GPF_TYPE == 'F' and attributes_dictionary["GPC_WHERE"] not in ['1', 'P']:
                InvalidAttribute("GPC_WHERE", attributes_dictionary["GPC_WHERE"], not_applicable=False)
            if GPF_object.GPF_TYPE == 'H' and attributes_dictionary["GPC_WHERE"] not in ['1', '2']:
                InvalidAttribute("GPC_WHERE", attributes_dictionary["GPC_WHERE"], not_applicable=False)
            if GPF_object.GPF_TYPE == 'Q' and attributes_dictionary["GPC_WHERE"] not in ['1', '2', '3', '4']:
                InvalidAttribute("GPC_WHERE", attributes_dictionary["GPC_WHERE"], not_applicable=False)
            if GPF_object.GPF_TYPE == 'S' and attributes_dictionary["GPC_WHERE"] not in ['1', '2', '3', '4', '5', '6',
                                                                                         '7', '8']:
                InvalidAttribute("GPC_WHERE", attributes_dictionary["GPC_WHERE"], not_applicable=False)
        # GPC_NAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["GPC_NAME"] not in PCF_attributes:
            UnmatchingForeignKey('GPC_NAME', attributes_dictionary["GPC_NAME"], 'PCF_NAME', 'PCF_table')
        # other attributes
        if attributes_dictionary["GPC_RAW"] not in ['C', ' ', 'U'] and attributes_dictionary["GPC_RAW"] != '':
            InvalidAttribute("GPC_RAW", attributes_dictionary["GPC_RAW"], not_applicable=False)
        if attributes_dictionary["GPC_PRCLR"] not in ['1', '2', '3', '4', '5', '6', '7']:
            InvalidAttribute("GPC_PRCLR", attributes_dictionary["GPC_PRCLR"], not_applicable=False)
        if attributes_dictionary["GPC_SYMB0"] not in ['0', '1', '2', '3', '4', '5', '6'] and attributes_dictionary[
            "GPC_SYMB0"] != '':
            InvalidAttribute("GPC_SYMB0", attributes_dictionary["GPC_SYMB0"], not_applicable=False)
        if attributes_dictionary["GPC_LINE"] not in ['0', '1', '2', '3', '4', '5'] and attributes_dictionary[
            "GPC_LINE"] != '':
            InvalidAttribute("GPC_LINE", attributes_dictionary["GPC_LINE"], not_applicable=False)
        if (int(attributes_dictionary["GPC_DOMAIN"]) < 0 or int
            (attributes_dictionary["GPC_DOMAIN"]) > pow(2, 16) - 1) and int(
            attributes_dictionary["GPC_DOMAIN"]) != 0:
            IntegerAttributeOutOfRange("GPC_DOMAIN", attributes_dictionary["GPC_DOMAIN"])

    elif class_type_str == "CUR":
        # CUR_PNAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["CUR_PNAME"] not in PCF_attributes:
            UnmatchingForeignKey('CUR_PNAME', attributes_dictionary["CUR_PNAME"], 'PCF_NAME', 'PCF_table')

        # CUR_SELECT
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["CUR_PNAME"])
        if PCF_object.PCF_CATEG == 'S':
            TXF_rows = session.query(schema.TXF).all()  # gets the TXF table
            TXF_attributes = []
            for TXF_object in TXF_rows:
                TXF_attributes.append(TXF_object.TXF_NUMBR)
            if attributes_dictionary["CUR_SELECT"] not in TXF_attributes:
                UnmatchingForeignKey('CUR_SELECT', attributes_dictionary["CUR_SELECT"], 'TXF_NUMBR', 'TXF_table')
        elif PCF_object.PCF_CATEG == 'N':
            CAF_rows = session.query(schema.CAF).all()  # gets the CAF table
            CAF_attributes = []
            for CAF_object in CAF_rows:
                CAF_attributes.append(CAF_object.CAF_NUMBR)
            MCF_rows = session.query(schema.MCF).all()  # gets the MCF table
            MCF_attributes = []
            for MCF_object in MCF_rows:
                MCF_attributes.append(MCF_object.MCF_IDENT)
            LGF_rows = session.query(schema.LGF).all()  # gets the LGF table
            LGF_attributes = []
            for LGF_object in LGF_rows:
                LGF_attributes.append(LGF_object.LGF_IDENT)
            if attributes_dictionary["CUR_SELECT"] not in CAF_attributes or attributes_dictionary[
                "CUR_SELECT"] not in MCF_attributes or attributes_dictionary["CUR_SELECT"] not in LGF_attributes:
                UnmatchingForeignKey('CUR_SELECT', attributes_dictionary["CUR_SELECT"],
                                     'CAF_NUMBR or MCF_IDENT or LGF_IDENT', 'CAF_table/ MCF_table/ LGF_table')

    elif class_type_str == "CVP":
        # CVP_TASK
        CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
        CCF_attributes = []
        CSF_rows = session.query(schema.CSF).all()  # gets the CSF table
        CSF_attributes = []
        for CCF_object in CCF_rows:
            CCF_attributes.append(CCF_object.CCF_CNAME)
        for CSF_object in CSF_rows:
            CSF_attributes.append(CSF_object.CSF_NAME)
        if attributes_dictionary["CVP_TASK"] not in CCF_attributes or attributes_dictionary[
            "CVP_TASK"] not in CSF_attributes:
            UnmatchingForeignKey('CVP_TASK', attributes_dictionary["CVP_TASK"], 'CCF_CNAME or CSF_NAME',
                                 'CCF_table/ CSF_table')

        # CVP_CVSID
        CVS_rows = session.query(schema.CVS).all()  # gets the CVS table
        CVS_attributes = []
        for CVS_object in CVS_rows:
            CVS_attributes.append(CVS_object.CVS_ID)
        if attributes_dictionary["CVP_CVSID"] not in CVS_attributes:
            UnmatchingForeignKey('CVP_CVSID', attributes_dictionary["CVP_CVSID"], 'CVS_ID', 'CVS_table')
        # other attributes
        if attributes_dictionary["CVP_TYPE"] not in ['C', 'S'] and attributes_dictionary["CVP_TYPE"] != '':
            InvalidAttribute("CVP_TYPE", attributes_dictionary["CVP_TYPE"], not_applicable=False)

    elif class_type_str == "DPC":
        # DPC_NUMBE
        DPF_rows = session.query(schema.DPF).all()  # gets the DPF table
        DPF_attributes = []
        for DPF_object in DPF_rows:
            DPF_attributes.append(DPF_object.DPF_NUMBE)
        if attributes_dictionary["DPC_NUMBE"] not in DPF_attributes:
            UnmatchingForeignKey('DPC_NUMBE', attributes_dictionary["DPC_NUMBE"], 'DPF_NUMBE', 'DPF_table')

        # DPC_NAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["DPC_NAME"] not in PCF_attributes and attributes_dictionary["DPC_NAME"] != '':
            UnmatchingForeignKey('DPC_NAME', attributes_dictionary["DPC_NAME"], 'PCF_NAME', 'PCF_table')
        # other attributes
        if int(attributes_dictionary["DPC_FLDN"]) < 0 or int(attributes_dictionary["DPC_FLDN"]) > 63:
            IntegerAttributeOutOfRange("DPC_FLDN", attributes_dictionary["DPC_FLDN"])
        if (int(attributes_dictionary["DPC_COMM"]) < 0 or int(attributes_dictionary["DPC_COMM"]) > 9999) and int(
                attributes_dictionary["DPC_COMM"]) != 0:
            IntegerAttributeOutOfRange("DPC_COMM", attributes_dictionary["DPC_COMM"])
        if attributes_dictionary["DPC_MODE"] not in ['Y', 'N'] and attributes_dictionary["DPC_MODE"] != '':
            InvalidAttribute("DPC_MODE", attributes_dictionary["DPC_MODE"], not_applicable=False)
        if attributes_dictionary["DPC_FORM"] not in ['B', 'O', 'D', 'H', 'N'] and attributes_dictionary[
            "DPC_FORM"] != '':
            InvalidAttribute("DPC_FORM", attributes_dictionary["DPC_FORM"], not_applicable=False)

    elif class_type_str == "CCA":
        if attributes_dictionary["CCA_ENGFMT"] not in ['I', 'U', 'R'] and attributes_dictionary["CCA_ENGFMT"] != '':
            InvalidAttribute("CCA_ENGFMT", attributes_dictionary["CCA_ENGFMT"], not_applicable=False)
        if attributes_dictionary["CCA_RAWFMT"] not in ['I', 'U', 'R'] and attributes_dictionary["CCA_RAWFMT"] != '':
            InvalidAttribute("CCA_RAWFMT", attributes_dictionary["CCA_RAWFMT"], not_applicable=False)
        if attributes_dictionary["CCA_RADIX"] not in ['D', 'H', 'O'] and attributes_dictionary["CCA_RADIX"] != '':
            InvalidAttribute("CCA_RADIX", attributes_dictionary["CCA_RADIX"], not_applicable=False)
        if attributes_dictionary["CCA_RAWFMT"] != 'U' and attributes_dictionary["CCA_RADIX"] != '':
            InvalidAttribute("CCA_RADIX", attributes_dictionary["CCA_RADIX"], not_applicable=True)

    elif class_type_str == "CCS":
        # CCS_NUMBR
        CCA_rows = session.query(schema.CCA).all()  # gets the CCA table
        CCA_attributes = []
        for CCA_object in CCA_rows:
            CCA_attributes.append(CCA_object.CCA_NUMBR)
        if attributes_dictionary["CCS_NUMBR"] not in CCA_attributes:
            UnmatchingForeignKey('CCS_NUMBR', attributes_dictionary["CCS_NUMBR"], 'CCA_NUMBR', 'CCA_table')

    elif class_type_str == "CPC":
        # CPC_DISPFMT
        if attributes_dictionary["CPC_DISPFMT"] not in ['A', 'I', 'U', 'R', 'T', 'D'] and attributes_dictionary[
            "CPC_DISPFMT"] != '':
            InvalidAttribute("CPC_DISPFMT", attributes_dictionary["CPC_DISPFMT"], not_applicable=False)
        if (attributes_dictionary["CPC_CATEG"] == 'A' or attributes_dictionary["CPC_CATEG"] == 'P' or int(
                attributes_dictionary["CPC_PTC"]) == 11) and attributes_dictionary["CPC_DISPFMT"] != '':
            print("CPC_DISPFMT changed to NULL")
            object_to_update.CPC_DISPFMT = None

        # CPC_PRFREF
        PRF_rows = session.query(schema.PRF).all()  # gets the PRF table
        PRF_attributes = []
        for PRF_object in PRF_rows:
            PRF_attributes.append(PRF_object.PRF_NUMBR)
        if attributes_dictionary["CPC_PRFREF"] not in PRF_attributes and attributes_dictionary["CPC_PRFREF"] != '':
            UnmatchingForeignKey('CPC_PRFREF', attributes_dictionary["CPC_PRFREF"], 'PRF_NUMBR', 'PRF_table')

        # CPC_CCAREF
        CCA_rows = session.query(schema.CCA).all()  # gets the CCA table
        CCA_attributes = []
        for CCA_object in CCA_rows:
            CCA_attributes.append(CCA_object.CCA_NUMBR)
        if attributes_dictionary["CPC_CATEG"] in ['A', 'P', 'N', 'T'] and attributes_dictionary["CPC_CCAREF"] != '':
            print("CPC_CCAREF changed to NULL")
            object_to_update.CPC_CCAREF = None
        if attributes_dictionary["CPC_CATEG"] in ['C', 'B'] and attributes_dictionary["CPC_CCAREF"] == '':
            InvalidAttribute("CPC_CCAREF", attributes_dictionary["CPC_CCAREF"], not_applicable=False)
        if attributes_dictionary["CPC_CCAREF"] not in CCA_attributes and attributes_dictionary["CPC_CCAREF"] != '':
            UnmatchingForeignKey('CPC_CCAREF', attributes_dictionary["CPC_CCAREF"], 'CCA_NUMBR', 'CCA_table')

        # CPC_PAFREF
        PAF_rows = session.query(schema.PAF).all()  # gets the PAF table
        PAF_attributes = []
        for PAF_object in PAF_rows:
            PAF_attributes.append(PAF_object.PAF_NUMBR)
        if attributes_dictionary["CPC_CATEG"] in ['A', 'P', 'N', 'C'] and attributes_dictionary["CPC_PAFREF"] != '':
            print("CPC_PAFREF changed to NULL")
            object_to_update.CPC_PAFREF = None
        if attributes_dictionary["CPC_CATEG"] in ['T', 'B'] and attributes_dictionary["CPC_PAFREF"] == '':
            InvalidAttribute("CPC_PAFREF", attributes_dictionary["CPC_PAFREF"], not_applicable=False)
        if attributes_dictionary["CPC_PAFREF"] not in PAF_attributes and attributes_dictionary["CPC_PAFREF"] != '':
            UnmatchingForeignKey('CPC_PAFREF', attributes_dictionary["CPC_PAFREF"], 'PAF_NUMBR', 'PAF_table')

        # CPC_DEFVAL
        if attributes_dictionary["CPC_CATEG"] == 'A':
            CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
            CCF_attributes = []
            for CCF_object in CCF_rows:
                CCF_attributes.append(CCF_object.CCF_CNAME)
            if attributes_dictionary["CPC_DEFVAL"] not in CCF_attributes and attributes_dictionary["CPC_DEFVAL"] != '':
                UnmatchingForeignKey('CPC_DEFVAL', attributes_dictionary["CPC_DEFVAL"], 'CCF_CNAME', 'CCF_table')
        if attributes_dictionary["CPC_CATEG"] == 'P':
            PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
            PCF_attributes = []
            for PCF_object in PCF_rows:
                if PCF_object.PCF_PID != None:  # PCF rows with PCF_PID not null
                    PCF_attributes.append(PCF_object.PCF_NAME)
            if attributes_dictionary["CPC_DEFVAL"] not in PCF_attributes and attributes_dictionary["CPC_DEFVAL"] != '':
                UnmatchingForeignKey('CPC_DEFVAL', attributes_dictionary["CPC_DEFVAL"], 'PCF_NAME', 'PCF_table')

        # CPC_CORR
        if attributes_dictionary["CPC_CORR"] not in ['Y', 'N'] and attributes_dictionary["CPC_CORR"] != '':
            InvalidAttribute("CPC_CORR", attributes_dictionary["CPC_CORR"], not_applicable=False)
        # PCF_object= session.query(schema.PCF).filter_by(¿?).first()
        # if int(PCF_object.PCF_PTC) == 10 and attributes_dictionary["CPC_CORR"] != 'N':
        # 	print("CPC_CORR changed to 'N'")
        # 	object_to_update.CPC_CORR= 'N'
        # other attributes
        if int(attributes_dictionary["CPC_PTC"]) < 1 or int(attributes_dictionary["CPC_PTC"]) > 13:
            IntegerAttributeOutOfRange("CPC_PTC", attributes_dictionary["CPC_PTC"])
        if checkAppendixA(attributes_dictionary["CPC_PTC"], attributes_dictionary["CPC_PFC"]) == False:
            IntegerAttributeOutOfRange("CPC_PFC", attributes_dictionary["CPC_PFC"])
        if attributes_dictionary["CPC_RADIX"] not in ['D', 'H', 'O'] and attributes_dictionary["CPC_RADIX"] != '':
            InvalidAttribute("CPC_RADIX", attributes_dictionary["CPC_RADIX"], not_applicable=False)
        if attributes_dictionary["CPC_CATEG"] not in ['C', 'T', 'B', 'A', 'P', 'N'] and attributes_dictionary[
            "CPC_CATEG"] != '':
            InvalidAttribute("CPC_CATEG", attributes_dictionary["CPC_CATEG"], not_applicable=False)
        if attributes_dictionary["CPC_CATEG"] == 'A' and (
                int(attributes_dictionary["CPC_PTC"]) != 7 or int(attributes_dictionary["CPC_PFC"]) != 0):
            print("CPC_PTC, CPC_PFC changed to 7, 0")
            object_to_update.CPC_PTC = 7
            object_to_update.CPC_PFC = 0
        if attributes_dictionary["CPC_CATEG"] == 'P' and int(attributes_dictionary["CPC_PTC"]) != 3:
            print("CPC_PTC changed to 3")
            object_to_update.CPC_PTC = 3
        if attributes_dictionary["CPC_INTER"] not in ['R', 'E'] and attributes_dictionary["CPC_INTER"] != '':
            InvalidAttribute("CPC_INTER", attributes_dictionary["CPC_INTER"], not_applicable=False)
        if attributes_dictionary["CPC_INTER"] == 'E' and attributes_dictionary["CPC_CATEG"] not in ['T', 'C']:
            InvalidAttribute("CPC_INTER", attributes_dictionary["CPC_INTER"], not_applicable=False)
        if attributes_dictionary["CPC_ENDIAN"] not in ['B', 'L'] and attributes_dictionary["CPC_ENDIAN"] != '':
            InvalidAttribute("CPC_ENDIAN", attributes_dictionary["CPC_ENDIAN"], not_applicable=False)

    elif class_type_str == "CDF":
        # CDF_CNAME
        CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
        CCF_attributes = []
        for CCF_object in CCF_rows:
            CCF_attributes.append(CCF_object.CCF_CNAME)
        if attributes_dictionary["CDF_CNAME"] not in CCF_attributes:
            UnmatchingForeignKey('CDF_CNAME', attributes_dictionary["CDF_CNAME"], 'CCF_CNAME', 'CCF_table')

        # CDF_PNAME
        if attributes_dictionary["CDF_ELTYPE"] in ['F', 'E']:
            CPC_rows = session.query(schema.CPC).all()  # gets the CPC table
            CPC_attributes = []
            for CPC_object in CPC_rows:
                CPC_attributes.append(CPC_object.CPC_PNAME)
            if attributes_dictionary["CDF_PNAME"] not in CPC_attributes:
                UnmatchingForeignKey('CDF_PNAME', attributes_dictionary["CDF_PNAME"], 'CPC_PNAME', 'CPC_table')

        # CDF_VALUE
        if attributes_dictionary["CDF_VALUE"] != '':
            CPC_object = session.query(schema.CPC).filter_by(CPC_PNAME=attributes_dictionary["CDF_PNAME"]).first()
            if CPC_object is None:
                UnmatchingForeignKey("CDF_VALUE", attributes_dictionary["CDF_VALUE"], "CPC_PNAME", "CPC_table")
            else:
                if CPC_object.CPC_CATEG == 'A':  # field shall contain the name of a command (CCF_CNAME)
                    CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
                    CCF_attributes = []
                    for CCF_object in CCF_rows:
                        CCF_attributes.append(CCF_object.CCF_CNAME)
                    if attributes_dictionary["CDF_VALUE"] not in CCF_attributes:
                        UnmatchingForeignKey('CDF_VALUE', attributes_dictionary["CDF_VALUE"], 'CCF_CNAME', 'CCF_table')

                # field shall contain the name of a monitoring parameter (PCF_NAME) with PCF_PID not null
                elif CPC_object.CPC_CATEG == 'P':
                    PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
                    PCF_attributes = []
                    for PCF_object in PCF_rows:
                        if PCF_object.PCF_PID != None:  # PCF rows with PCF_PID not null
                            PCF_attributes.append(PCF_object.PCF_NAME)
                    if attributes_dictionary["CAF_VALUE"] not in PCF_attributes:
                        UnmatchingForeignKey('CAF_VALUE', attributes_dictionary["CAF_VALUE"], 'PCF_NAME', 'PCF_table')
        if attributes_dictionary["CDF_VALUE"] == '':
            if attributes_dictionary["CDF_ELTYPE"] == 'A' or (
                    attributes_dictionary["CDF_ELTYPE"] == 'F' and attributes_dictionary["CDF_INTER"] != 'D') or (
                    attributes_dictionary["CDF_ELTYPE"] == 'E' and attributes_dictionary["CDF_INTER"] == 'T'):
                InvalidAttribute("CDF_VALUE", attributes_dictionary["CDF_VALUE"], not_applicable=False)
            if attributes_dictionary["CDF_ELTYPE"] == 'E' and attributes_dictionary["CDF_INTER"] != 'T':
                # The user must enter a value before loading the command
                InvalidAttribute("CDF_VALUE", attributes_dictionary["CDF_VALUE"], not_applicable=False,
                                 full_message='The user must enter a value before loading the command')

        # CDF_TMID
        if attributes_dictionary["CDF_INTER"] == 'T' and attributes_dictionary["CDF_TMID"] != '':
            PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
            PCF_attributes = []
            for PCF_object in PCF_rows:
                PCF_attributes.append(PCF_object.PCF_NAME)
            if attributes_dictionary["CDF_TMID"] not in PCF_attributes:
                UnmatchingForeignKey('CDF_TMID', attributes_dictionary["CDF_TMID"], 'PCF_NAME', 'PCF_table')
            PCF_cdf_tmid = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["CDF_TMID"]).first()
            PCF_cdf_pname = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["CDF_PNAME"]).first()
            if PCF_cdf_tmid is None:
                UnmatchingForeignKey("CDF_TMID", attributes_dictionary["CDF_TMID"], "PCF_NAME", "PCF_table")
            else:
                if PCF_cdf_pname is None:
                    UnmatchingForeignKey("CDF_PNAME", attributes_dictionary["CDF_PNAME"], "PCF_NAME", "PCF_table")
                else:
                    if PCF_cdf_tmid.PCF_PTC != PCF_cdf_pname.PCF_PTC or PCF_cdf_tmid.PCF_PFC != PCF_cdf_pname.PCF_PFC:
                        print("PCF_PTC, PCF_PFC attributes of row %s changed to %s, %s" % (str(PCF_cdf_tmid.PCF_NAME)),
                              str(PCF_cdf_pname.PCF_PTC), str(PCF_cdf_pname.PCF_PFC))
                        session.delete(PCF_cdf_tmid)  # changes attributes of object in PCF table
                        session.commit()
                        session.make_transient(PCF_cdf_tmid)
                        PCF_cdf_tmid.PCF_PTC = PCF_cdf_pname.PCF_PTC
                        PCF_cdf_tmid.PCF_PFC = PCF_cdf_pname.PCF_PFC
                        session.add(PCF_cdf_tmid)
        if attributes_dictionary["CDF_INTER"] != 'T' and attributes_dictionary["CDF_TMID"] != '':
            InvalidAttribute("CDF_TMID", attributes_dictionary["CDF_TMID"], not_applicable=True)

        # other attributes
        if attributes_dictionary["CDF_ELTYPE"] not in ['A', 'F', 'E']:
            InvalidAttribute("CDF_ELTYPE", attributes_dictionary["CDF_ELTYPE"], not_applicable=False)
        if attributes_dictionary["CDF_DESCR"] != '' and attributes_dictionary["CDF_ELTYPE"] != 'A':
            InvalidAttribute("CDF_DESCR", attributes_dictionary["CDF_DESCR"], not_applicable=True)
        if int(attributes_dictionary["CDF_BIT"]) < 0:
            IntegerAttributeOutOfRange("CDF_BIT", attributes_dictionary["CDF_BIT"])
        if attributes_dictionary["CDF_INTER"] not in ['R', 'D', 'T', 'E'] and attributes_dictionary["CDF_INTER"] != '':
            InvalidAttribute("CDF_INTER", attributes_dictionary["CDF_INTER"], not_applicable=False)

    elif class_type_str == "CVE":

        # CVE_CVSID
        CVS_rows = session.query(schema.CVS).all()  # gets the CVS table
        CVS_attributes = []
        for CVS_object in CVS_rows:
            if CVS_object.CVS_SOURCE == 'V':  # only rows with CVS_SOURCE = 'V'
                CVS_attributes.append(CVS_object.CVS_ID)
        if attributes_dictionary["CVE_CVSID"] not in CVS_attributes:
            UnmatchingForeignKey('CVE_CVSID', attributes_dictionary["CVE_CVSID"], "CVS_ID with CVS_SOURCE = 'V'",
                                 'CVS_table')
        # CVE_PARNAM**********
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["CVE_PARNAM"] not in PCF_attributes:
            UnmatchingForeignKey('CVE_PARNAM', attributes_dictionary["CVE_PARNAM"], 'PCF_NAME', 'PCF_table')
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["CVE_PARNAM"]).first()
        OCF_object = session.query(schema.OCF).filter_by(OCF_NAME=attributes_dictionary["CVE_PARNAM"]).first()

        if PCF_object is None:
            UnmatchingForeignKey("CVE_PARNAM", attributes_dictionary["CVE_PARNAM"], "PCF_NAME", "PCF_table")
        else:
            if PCF_object is None:
                UnmatchingForeignKey("CVE_PARNAM", attributes_dictionary["CVE_PARNAM"], "OCF_NAME", "OCF_table")
            else:
                if PCF_object.PCF_USCON == 'Y' and attributes_dictionary["CVE_INTER"] != OCF_object.OCF_INTER:
                    print("CVE_INTER changed to %s" % str(OCF_object.OCF_INTER))
                    object_to_update.CVE_INTER = OCF_object.OCF_INTER

        # CVE_INTER
        if attributes_dictionary["CVE_INTER"] not in ['R', 'E', 'C'] and attributes_dictionary["CVE_INTER"] != '':
            InvalidAttribute("CVE_INTER", attributes_dictionary["CVE_INTER"], not_applicable=False)
        if attributes_dictionary["CVE_INTER"] == 'E':
            CVE_list = session.query(schema.CVE).filter_by(CVE_PARNAM=attributes_dictionary["CVE_PARMAN"]).all()
            for CVE_object in CVE_list:  # all rows must have the same representation
                if CVE_object.CVE_INTER != attributes_dictionary["CVE_INTER"]:
                    InvalidAttribute("CVE_INTER", attributes_dictionary["CVE_INTER"], not_applicable=False)
        # CVE_VAL
        if attributes_dictionary["CVE_CHECK"] != 'B' and attributes_dictionary["CVE_VAL"] != '':
            InvalidAttribute("CVE_VAL", attributes_dictionary["CVE_VAL"], not_applicable=True)
        if attributes_dictionary["CVE_CHECK"] == 'B' and attributes_dictionary["CVE_VAL"] == '':
            InvalidAttribute("CVE_VAL", attributes_dictionary["CVE_VAL"], not_applicable=False)
        # if attributes_dictionary["CVE_CHECK"] == 'B' and attributes_dictionary["CVE_VAL"] != '':

        # CVE_TOL
        PCF_object = session.query(schema.PCF).filter_by(PCF_NAME=attributes_dictionary["CVE_PARNAM"]).first()
        if PCF_object is None:
            UnmatchingForeignKey("CVE_PARNAM", attributes_dictionary["CVE_PARNAM"], "PCF_NAME", "PCF_table")
        else:
            if attributes_dictionary["CVE_INTER"] == 'E' and PCF_object.PCF_CATEG == 'S' \
                    and attributes_dictionary["CVE_TOL"] != '':
                # field must be left null
                InvalidAttribute("CVE_TOL", attributes_dictionary["CVE_TOL"], not_applicable=False)

        # CVE_CHECK
        if attributes_dictionary["CVE_CHECK"] not in ['B', 'S'] and attributes_dictionary["CVE_CHECK"] != '':
            InvalidAttribute("CVE_CHECK", attributes_dictionary["CVE_CHECK"], not_applicable=False)

    elif class_type_str == "PRF":
        if attributes_dictionary["PRF_INTER"] not in ['R', 'E'] and attributes_dictionary["PRF_INTER"] != '':
            InvalidAttribute("PRF_INTER", attributes_dictionary["PRF_INTER"], not_applicable=False)
        if attributes_dictionary["PRF_DSPFMT"] not in ['A', 'I', 'U', 'R', 'T', 'D'] and attributes_dictionary[
            "PRF_DSPFMT"] != '':
            InvalidAttribute("PRF_DSPFMT", attributes_dictionary["PRF_DSPFMT"], not_applicable=False)
        if attributes_dictionary["PRF_DSPFMT"] != 'U' and attributes_dictionary["PRF_RADIX"] != '':
            InvalidAttribute("PRF_RADIX", attributes_dictionary["PRF_RADIX"], not_applicable=True)
        if attributes_dictionary["PRF_RADIX"] not in ['D', 'H', 'O'] and attributes_dictionary["PRF_RADIX"] != '':
            InvalidAttribute("PRF_RADIX", attributes_dictionary["PRF_RADIX"], not_applicable=False)

    elif class_type_str == "PRV":
        # PRV_NUMBR
        PRF_rows = session.query(schema.PRF).all()  # gets the PRF table
        PRF_attributes = []
        for PRF_object in PRF_rows:
            PRF_attributes.append(PRF_object.PRF_NUMBR)
        if attributes_dictionary["PRV_NUMBR"] not in PRF_attributes:
            UnmatchingForeignKey('PRV_NUMBR', attributes_dictionary["PRV_NUMBR"], 'PRF_NUMBR', 'PRF_table')

    elif class_type_str == "CSP":
        # CSP_SQNAME
        CSF_rows = session.query(schema.CSF).all()  # gets the CSF table
        CSF_attributes = []
        for CSF_object in CSF_rows:
            CSF_attributes.append(CSF_object.CSF_NAME)
        if attributes_dictionary["CSP_SQNAME"] not in CSF_attributes:
            UnmatchingForeignKey('CSP_SQNAME', attributes_dictionary["CSP_SQNAME"], 'CSF_NAME', 'CSF_table')

        # CSP_VTYPE
        if attributes_dictionary["CSP_VTYPE"] not in ['R', 'E'] and attributes_dictionary["CSP_VTYPE"] != '':
            InvalidAttribute("CSP_VTYPE", attributes_dictionary["CSP_VTYPE"], not_applicable=False)
        if attributes_dictionary["CSP_VTYPE"] == 'E' and attributes_dictionary["CSP_CATEG"] not in ['T', 'C']:
            InvalidAttribute("CSP_VTYPE", attributes_dictionary["CSP_VTYPE"], not_applicable=False)
        if attributes_dictionary["CSP_VTYPE"] == '' and attributes_dictionary["CSP_TYPE"] == 'P' and \
                attributes_dictionary["CSP_DEFVAL"] != '':
            InvalidAttribute("CSP_VTYPE", attributes_dictionary["CSP_VTYPE"], not_applicable=False)
        if attributes_dictionary["CSP_TYPE"] in ['C', 'S'] and attributes_dictionary[
            "CSP_VTYPE"] != '':  # must be left null
            print("CSP_VTYPE changed to NULL")
            object_to_update.CSP_VTYPE = None

        # CSP_DEFVAL
        if attributes_dictionary["CSP_CATEG"] == 'A' and attributes_dictionary["CSP_DEFVAL"] != '':
            CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
            CCF_attributes = []
            for CCF_object in CCF_rows:
                CCF_attributes.append(CCF_object.CCF_CNAME)
            if attributes_dictionary["CSP_DEFVAL"] not in CCF_attributes:
                UnmatchingForeignKey('CSP_DEFVAL', attributes_dictionary["CSP_DEFVAL"], 'CCF_CNAME', 'CCF_table')
        if attributes_dictionary["CSP_CATEG"] == 'P' and attributes_dictionary["CSP_DEFVAL"] != '':
            PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
            PCF_attributes = []
            for PCF_object in PCF_rows:
                if PCF_object.PCF_PID != None:  # PCF rows with PCF_PID not null
                    PCF_attributes.append(PCF_object.PCF_NAME)
            if attributes_dictionary["CSP_DEFVAL"] not in PCF_attributes:
                UnmatchingForeignKey('CSP_DEFVAL', attributes_dictionary["CSP_DEFVAL"], 'PCF_NAME', 'PCF_table')
        if attributes_dictionary["CSP_TYPE"] == 'C' and attributes_dictionary["CSP_DEFVAL"] != '':
            CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
            CCF_attributes = []
            for CCF_object in CCF_rows:
                CCF_attributes.append(CCF_object.CCF_CNAME)
            if attributes_dictionary["CSP_DEFVAL"] not in CCF_attributes:
                UnmatchingForeignKey('CSP_DEFVAL', attributes_dictionary["CSP_DEFVAL"], 'CCF_CNAME', 'CCF_table')
        if attributes_dictionary["CSP_TYPE"] == 'S' and attributes_dictionary["CSP_DEFVAL"] != '':
            CSF_rows = session.query(schema.CSF).all()  # gets the CSF table
            CSF_attributes = []
            for CSF_object in CSF_rows:
                CSF_attributes.append(CSF_object.CSF_NAME)
            if attributes_dictionary["CSP_DEFVAL"] not in CSF_attributes:
                UnmatchingForeignKey('CSP_DEFVAL', attributes_dictionary["CSP_DEFVAL"], 'CSF_NAME', 'CSF_table')
        if attributes_dictionary["CSP_DEFVAL"] == '':
            # The user must enter a value before loading the command
            InvalidAttribute("CSP_DEFVAL", attributes_dictionary["CSP_DEFVAL"], not_applicable=False,
                             full_message='The user must enter a value before loading the command')

        # CSP_PRFREF
        PRF_rows = session.query(schema.PRF).all()  # gets the PRF table
        PRF_attributes = []
        for PRF_object in PRF_rows:
            PRF_attributes.append(PRF_object.PRF_NUMBR)
        if attributes_dictionary["CSP_PRFREF"] not in PRF_attributes and attributes_dictionary["CSP_PRFREF"] != '':
            UnmatchingForeignKey('CSP_PRFREF', attributes_dictionary["CSP_PRFREF"], 'PRF_NUMBR', 'PRF_table')
        if attributes_dictionary["CSP_TYPE"] in ['C', 'S'] and attributes_dictionary["CSP_PRFREF"] != '':
            print("CSP_PRFREF changed to NULL")
            object_to_update.CSP_PRFREF = None

        # CSP_CCAREF
        CCA_rows = session.query(schema.CCA).all()  # gets the CCA table
        CCA_attributes = []
        for CCA_object in CCA_rows:
            CCA_attributes.append(CCA_object.CCA_NUMBR)
        if attributes_dictionary["CSP_CCAREF"] not in CCA_attributes and attributes_dictionary["CSP_CCAREF"] != '':
            UnmatchingForeignKey('CSP_CCAREF', attributes_dictionary["CSP_CCAREF"], 'CCA_NUMBR', 'CCA_table')
        if (attributes_dictionary["CSP_CATEG"] in ['', 'A', 'P', 'N', 'T'] or attributes_dictionary["CSP_TYPE"] in ['C',
                                                                                                                    'S']) and \
                attributes_dictionary["CSP_CCAREF"] != '':
            print("CSP_CCAREF changed to NULL")
            object_to_update.CSP_CCAREF = None
        if attributes_dictionary["CSP_CATEG"] in ['C', 'B'] and attributes_dictionary["CSP_CCAREF"] == '':
            InvalidAttribute("CSP_CCAREF", attributes_dictionary["CSP_CCAREF"], not_applicable=False)

        # CSP_PAFREF
        PAF_rows = session.query(schema.PAF).all()  # gets the PAF table
        PAF_attributes = []
        for PAF_object in PAF_rows:
            PAF_attributes.append(PAF_object.PAF_NUMBR)
        if attributes_dictionary["CSP_PAFREF"] not in PAF_attributes and attributes_dictionary["CSP_PAFREF"] != '':
            UnmatchingForeignKey('CSP_PAFREF', attributes_dictionary["CSP_PAFREF"], 'PAF_NUMBR', 'PAF_table')
        if (attributes_dictionary["CSP_CATEG"] in ['', 'A', 'P', 'N', 'C'] or attributes_dictionary["CSP_TYPE"] in ['C',
                                                                                                                    'S']) and \
                attributes_dictionary["CSP_CCAREF"] != '':
            print("CSP_PAFREF changed to NULL")
            object_to_update.CSP_PAFREF = None
        if attributes_dictionary["CSP_CATEG"] in ['T', 'B'] and attributes_dictionary["CSP_PAFREF"] == '':
            InvalidAttribute("CSP_PAFREF", attributes_dictionary["CSP_PAFREF"], not_applicable=False)

        # CSP_DISPFMT
        if attributes_dictionary["CSP_DISPFMT"] not in ['I', 'U', 'A', 'R', 'T', 'D'] and \
                attributes_dictionary["CSP_DISPFMT"] != '':
            InvalidAttribute("CSP_DISPFMT", attributes_dictionary["CSP_DISPFMT"], not_applicable=False)
        CCA_object = session.query(schema.CCA).filter_by(CCA_NUMBR=attributes_dictionary["CSP_CCAREF"]).first()
        if CCA_object is None:
            UnmatchingForeignKey("CSP_CCAREF", attributes_dictionary["CSP_CCAREF"], "CCA_NUMBR", "CCA_table")
        else:
            if attributes_dictionary["CSP_CATEG"] == 'T' and attributes_dictionary["CSP_DISPFMT"] != 'A':
                print("CSP_DISPFMT changed to 'A'")
                object_to_update.CSP_DISPFMT = 'A'
            if attributes_dictionary["CSP_CATEG"] == 'C' and CCA_object.CCA_ENGFMT == 'I' and attributes_dictionary[
                "CSP_DISPFMT"] != 'I':
                print("CSP_DISPFMT changed to 'I'")
                object_to_update.CSP_DISPFMT = 'I'
            if attributes_dictionary["CSP_CATEG"] == 'C' and CCA_object.CCA_ENGFMT == 'U' and attributes_dictionary[
                "CSP_DISPFMT"] != 'U':
                print("CSP_DISPFMT changed to 'U'")
                object_to_update.CSP_DISPFMT = 'U'
            if attributes_dictionary["CSP_CATEG"] == 'C' and CCA_object.CCA_ENGFMT == 'R' and attributes_dictionary[
                "CSP_DISPFMT"] != 'R':
                print("CSP_DISPFMT changed to 'R'")
                object_to_update.CSP_DISPFMT = 'R'
            if int(attributes_dictionary["CSP_PTC"]) == 9 and attributes_dictionary["CSP_DISPFMT"] != 'T':
                print("CSP_DISPFMT changed to 'T'")
                object_to_update.CSP_DISPFMT = 'T'
            if int(attributes_dictionary["CSP_PTC"]) == 10 and attributes_dictionary["CSP_DISPFMT"] != 'D':
                print("CSP_DISPFMT changed to 'D'")
                object_to_update.CSP_DISPFMT = 'D'
            if (attributes_dictionary["CSP_CATEG"] == 'A' or attributes_dictionary["CSP_CATEG"] == 'P') and \
                    attributes_dictionary["CSP_DISPFMT"] != '':
                print("CSP_DISPFMT changed to NULL")
                object_to_update.CSP_DISPFMT = None

        # Other attributes
        if int(attributes_dictionary["CSP_FPNUM"]) < 0 or int(attributes_dictionary["CSP_FPNUM"]) > 65535:
            IntegerAttributeOutOfRange("CSP_FPNUM", attributes_dictionary["CSP_FPNUM"])
        if int(attributes_dictionary["CSP_PTC"]) < 1 or int(attributes_dictionary["CSP_PTC"]) > 13:
            IntegerAttributeOutOfRange("CSP_PTC", attributes_dictionary["CSP_PTC"])
        if checkAppendixA(int(attributes_dictionary["CSP_PTC"]), int(attributes_dictionary["CSP_PFC"])) == False:
            IntegerAttributeOutOfRange("CSP_PFC", attributes_dictionary["CSP_PFC"])
        if attributes_dictionary["CSP_RADIX"] not in ['D', 'H', 'O'] and attributes_dictionary["CSP_RADIX"] != '':
            InvalidAttribute("CSP_RADIX", attributes_dictionary["CSP_RADIX"], not_applicable=False)
        if attributes_dictionary["CSP_TYPE"] not in ['C', 'S', 'P']:
            InvalidAttribute("CSP_TYPE", attributes_dictionary["CSP_TYPE"], not_applicable=False)
        if attributes_dictionary["CSP_CATEG"] not in ['C', 'T', 'A', 'P', 'B'] and attributes_dictionary[
            "CSP_CATEG"] != '':
            InvalidAttribute("CSP_CATEG", attributes_dictionary["CSP_CATEG"], not_applicable=False)
        if attributes_dictionary["CSP_CATEG"] == 'A' and (
                int(attributes_dictionary["CSP_PTC"]) != 7 or int(attributes_dictionary["CSP_PTC"]) != 0):
            print("CSP_PTC, CSP_PFC values changed to 7, 0")
            object_to_update.CSP_PTC = 7
            object_to_update.CSP_PFC = 0
        if attributes_dictionary["CSP_CATEG"] == 'P' and int(attributes_dictionary["CSP_PTC"]) != 3:
            print("CSP_PTC value changed to 3")
            object_to_update.CSP_PTC = 3

    elif class_type_str == "SDF":
        # SDF_SQNAME
        CSF_rows = session.query(schema.CSF).all()  # gets the CSF table
        CSF_attributes = []
        for CSF_object in CSF_rows:
            CSF_attributes.append(CSF_object.CSF_NAME)
        if attributes_dictionary["SDF_SQNAME"] not in CSF_attributes:
            UnmatchingForeignKey('SDF_SQNAME', attributes_dictionary["SDF_SQNAME"], 'CSF_NAME', 'CSF_table')
        # SDF_ENTRY
        CSS_rows = session.query(schema.CSS).all()  # gets the CSS table
        CSS_attributes = []
        for CSS_object in CSS_rows:
            if CSS_object.CSS_TYPE in ['C', 'S']:
                CSS_attributes.append(CSS_object.CSS_ENTRY)
        if attributes_dictionary["SDF_ENTRY"] not in CSS_attributes:
            UnmatchingForeignKey('SDF_ENTRY', attributes_dictionary["SDF_ENTRY"], 'CSS_ENTRY', 'CSS_table')

        # SDF_ELEMID
        CSS_rows = session.query(schema.CSS).all()  # gets the CSS table
        CSS_attributes = []
        for CSS_object in CSS_rows:
            CSS_attributes.append(CSS_object.CSS_ELEMID)
        if attributes_dictionary["SDF_ELEMID"] not in CSS_attributes:
            UnmatchingForeignKey('SDF_ELEMID', attributes_dictionary["SDF_ELEMID"], 'CSS_ELEMID', 'CSS_table')

        # SDF_PNAME
        CSS_object = session.query(schema.CSS).filter_by(CSS_ENTRY=attributes_dictionary["SDF_ENTRY"])
        if CSS_object.CSS_TYPE == 'C':  # command
            element_type = 'command'
        if CSS_object.CSS_TYPE == 'S':  # sequence
            element_type = 'sequence'
        if element_type == 'command':
            CDF_rows = session.query(schema.CDF).all()  # gets the CDF table
            CDF_attributes = []
            for CDF_object in CDF_rows:
                if CDF_object.CDF_ELTYPE == 'E':
                    CDF_attributes.append(CDF_object.CDF_PNAME)
            if attributes_dictionary["SDF_PNAME"] not in CDF_attributes:
                UnmatchingForeignKey('SDF_PNAME', attributes_dictionary["SDF_PNAME"], "CDF_PNAME with CDF_ELTYPE= 'E'",
                                     'CDF_table')
        if element_type == 'sequence':
            CSP_rows = session.query(schema.CSP).all()  # gets the CSP table
            CSP_attributes = []
            for CSP_object in CSP_rows:
                CSP_attributes.append(CSP_object.CSP_FPNAME)
            if attributes_dictionary["SDF_PNAME"] not in CSP_attributes:
                UnmatchingForeignKey('SDF_PNAME', attributes_dictionary["SDF_PNAME"], 'CSP_FPNAME', 'CSP_table')

        # SDF_VTYPE
        if attributes_dictionary["SDF_VTYPE"] not in ['R', 'E', 'F', 'P', 'S', 'D']:
            InvalidAttribute("SDF_VTYPE", attributes_dictionary["SDF_VTYPE"], not_applicable=False)
        if element_type == 'command':
            CPC_object = session.query(schema.CPC).filter_by(
                CPC_PNAME=attributes_dictionary["SDF_PNAME"]).first()  # *unchanged*
            CDF_object = session.query(schema.CDF).filter_by(
                CDF_PNAME=attributes_dictionary["SDF_PNAME"]).first()  # *unchanged*
            categ = CPC_object.CPC_CATEG
            grpsize = int(CDF_object.CDF_GRPSIZE)
        if element_type == 'sequence':
            CSP_object = session.query(schema.CSP).filter_by(
                CSC_FPNAME=attributes_dictionary["SDF_PNAME"]).first()  # *unchanged*
            categ = CSP_object.CSP_CATEG
            grpsize = 0
        if attributes_dictionary["SDF_VTYPE"] == 'E' and categ not in ['T', 'C']:
            InvalidAttribute("SDF_VTYPE", attributes_dictionary["SDF_VTYPE"], not_applicable=False)
        if attributes_dictionary["SDF_VTYPE"] == 'F' and grpsize > 0:
            InvalidAttribute("SDF_VTYPE", attributes_dictionary["SDF_VTYPE"], not_applicable=False)
        if attributes_dictionary["SDF_VTYPE"] == 'S' and CSP_object.CSP_DEFVAL is None:
            InvalidAttribute("SDF_VTYPE", attributes_dictionary["SDF_VTYPE"], not_applicable=False,
                             full_message="CSP_DEFVAL cannot be left null.")
        # SDF_VALUE
        if attributes_dictionary["SDF_VTYPE"] == 'R' and categ == 'A':
            CCF_rows = session.query(schema.CCF).all()  # gets the CCF table
            CCF_attributes = []
            for CCF_object in CCF_rows:
                CCF_attributes.append(CCF_object.CCF_CNAME)
            if attributes_dictionary["SDF_VALUE"] not in CCF_attributes and attributes_dictionary["SDF_VALUE"] != '':
                UnmatchingForeignKey('SDF_VALUE', attributes_dictionary["SDF_VALUE"], 'CCF_CNAME', 'CCF_table')
        if attributes_dictionary["SDF_VTYPE"] == 'R' and categ == 'P':
            PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
            PCF_attributes = []
            for PCF_object in PCF_rows:
                if PCF_object.PCF_PID != None:
                    PCF_attributes.append(PCF_object.PCF_NAME)
            if attributes_dictionary["SDF_VALUE"] not in PCF_attributes and attributes_dictionary["SDF_VALUE"] != '':
                UnmatchingForeignKey('SDF_VALUE', attributes_dictionary["SDF_VALUE"], 'PCF_NAME', 'PCF_table')
        if attributes_dictionary["SDF_VTYPE"] == 'F':
            CSP_rows = session.query(schema.CSP).all()  # gets the CSP table
            CSP_attributes = []
            for CSP_object in CSP_rows:
                CSP_attributes.append(CSP_object.CSP_FPNAME)
            if attributes_dictionary["SDF_VALUE"] not in CSP_attributes and attributes_dictionary["SDF_VALUE"] != '':
                UnmatchingForeignKey('SDF_VALUE', attributes_dictionary["SDF_VALUE"], 'CSP_FPNAME', 'CSP_table')
        if attributes_dictionary["SDF_VALUE"] == '' and attributes_dictionary["SDF_VTYPE"] not in ['D', 'P', 'S']:
            InvalidAttribute("SDF_VALUE", attributes_dictionary["SDF_VALUE"], not_applicable=False)
        # SDF_VALSET
        if attributes_dictionary["SDF_VTYPE"] == 'P':
            PSV_rows = session.query(schema.PSV).all()  # gets the PSV table
            PSV_attributes = []
            for PSV_object in PSV_rows:
                PSV_attributes.append(PSV_object.PSV_PVSID)
            if attributes_dictionary["SDF_VALSET"] not in PSV_attributes:
                UnmatchingForeignKey('SDF_VALSET', attributes_dictionary["SDF_VALSET"], 'PSV_PVSID', 'PSV_table')
        if attributes_dictionary["SDF_VTYPE"] != 'P' and attributes_dictionary["SDF_VALSET"] != '':
            InvalidAttribute("SDF_VALSET", attributes_dictionary["SDF_VALSET"], not_applicable=True)
        # Other parameters
        if attributes_dictionary["SDF_FTYPE"] not in ['F', 'E'] and attributes_dictionary["SDF_FTYPE"] != '':
            InvalidAttribute("SDF_FTYPE", attributes_dictionary["SDF_FTYPE"], not_applicable=False)
        if attributes_dictionary["SDF_VTYPE"] not in ['R', 'E', 'F', 'P', 'S', 'D']:
            InvalidAttribute("SDF_VTYPE", attributes_dictionary["SDF_VTYPE"], not_applicable=False)

    elif class_type_str == "PVS":
        # PVS_ID
        PSV_rows = session.query(schema.PSV).all()  # gets the PSV table
        PSV_attributes = []
        for PSV_object in PSV_rows:
            PSV_attributes.append(PSV_object.PSV_PVSID)
        if attributes_dictionary["PVS_ID"] not in PSV_attributes:
            UnmatchingForeignKey('PVS_ID', attributes_dictionary["PVS_ID"], 'PSV_PVSID', 'PSV_table')

        # PVS_PSID
        PST_rows = session.query(schema.PST).all()  # gets the PST table
        PST_attributes = []
        for PST_object in PST_rows:
            PST_attributes.append(PST_object.PST_NAME)
        if attributes_dictionary["PVS_PSID"] not in PST_attributes:
            UnmatchingForeignKey('PVS_PSID', attributes_dictionary["PVS_PSID"], 'PST_NAME', 'PST_table')

        # PVS_PNAME
        CDF_rows = session.query(schema.CDF).all()  # gets the CDF table
        CDF_attributes = []
        CSP_rows = session.query(schema.CSP).all()  # gets the CSP table
        CSP_attributes = []
        for CDF_object in CDF_rows:
            CDF_attributes.append(CDF_object.CDF_PNAME)
        for CSP_object in CSP_rows:
            CSP_attributes.append(CSP_object.CSP_FPNAME)
        if attributes_dictionary["PVS_PNAME"] not in CDF_attributes and attributes_dictionary[
            "PVS_PNAME"] not in CSP_attributes:
            UnmatchingForeignKey('PVS_PNAME', attributes_dictionary["PVS_PNAME"], 'CDF_PNAME/ CSP_FPNAME',
                                 'CDF_table/ CSP_table')
        # PVS_INTER
        if attributes_dictionary["PVS_PNAME"] in CDF_attributes:
            CPC_object = session.query(schema.CPC).filter_by(
                CPC_PNAME=attributes_dictionary["PVS_PNAME"]).first()  # *unchanged*
            categ = CPC_object.CPC_CATEG
        if attributes_dictionary["PVS_PNAME"] in CSP_attributes:
            CSP_object = session.query(schema.CSP).filter_by(
                CSP_FPNAME=attributes_dictionary["PVS_PNAME"]).first()  # *unchanged*
            categ = CSP_object.CSP_CATEG
        if attributes_dictionary["PVS_INTER"] not in ['R', 'E'] and attributes_dictionary["PVS_INTER"] != '':
            InvalidAttribute("PVS_INTER", attributes_dictionary["PVS_INTER"], not_applicable=False)
        if attributes_dictionary["PVS_INTER"] == 'E' and categ not in ['T', 'C']:
            InvalidAttribute("PVS_INTER", attributes_dictionary["PVS_INTER"], not_applicable=False)
    # PVS_BIT
    # if attributes_dictionary["PVS_PNAME"] in CDF_attributes: # command
    # 	pass
    # if attributes_dictionary["PVS_PNAME"] in CSP_attributes: # sequence
    # 	pass

    elif class_type_str == "VDF":
        if (int(attributes_dictionary["VDF_RELEASE"]) < 0 or int(attributes_dictionary["VDF_RELEASE"]) >
                                      pow(2, 16) - 1) and int(attributes_dictionary["VDF_RELEASE"]) != 0:
            IntegerAttributeOutOfRange("VDF_RELEASE", attributes_dictionary["VDF_RELEASE"])
        if (int(attributes_dictionary["VDF_ISSUE"]) < 0 or int(attributes_dictionary["VDF_ISSUE"])
            > pow(2, 16) - 1) and int(attributes_dictionary["VDF_RELEASE"]) != 0:
            IntegerAttributeOutOfRange("VDF_ISSUE", attributes_dictionary["VDF_ISSUE"])

    elif class_type_str == "MCF":
        pass

    elif class_type_str == "LGF":
        pass

    elif class_type_str == "PIC":
        if int(attributes_dictionary["PIC_TYPE"]) < 0 or int(attributes_dictionary["PIC_TYPE"]) > 255:
            IntegerAttributeOutOfRange("PIC_TYPE", attributes_dictionary["PIC_TYPE"])
        if int(attributes_dictionary["PIC_STYPE"]) < 0 or int(attributes_dictionary["PIC_STYPE"]) > 255:
            IntegerAttributeOutOfRange("PIC_STYPE", attributes_dictionary["PIC_STYPE"])

    elif class_type_str == "PPF":
        if (int(attributes_dictionary["PPF_NBPR"]) < 1 or int(attributes_dictionary["PPF_NBPR"]) > 32) and int(
                attributes_dictionary["PPF_NBPR"]) != 0:
            IntegerAttributeOutOfRange("PPF_NBPR", attributes_dictionary["PPF_NBPR"])

    elif class_type_str == "PPC":
        # PPC_NUMBE
        PPF_rows = session.query(schema.PPF).all()  # gets the PPF table
        PPF_attributes = []
        for PPF_object in PPF_rows:
            PPF_attributes.append(PPF_object.PPF_NUMBE)
        if attributes_dictionary["PPC_NUMBE"] not in PPF_attributes:
            UnmatchingForeignKey('PPC_NUMBE', attributes_dictionary["PPC_NUMBE"], 'PPF_NUMBE', 'PPF_table')
        
        # PPC_NAME
        PCF_rows = session.query(schema.PCF).all()  # gets the PCF table
        PCF_attributes = []
        for PCF_object in PCF_rows:
            PCF_attributes.append(PCF_object.PCF_NAME)
        if attributes_dictionary["PPC_NAME"] not in PCF_attributes:
            UnmatchingForeignKey('PPC_NAME', attributes_dictionary["PPC_NAME"], 'PCF_NAME', 'PCF_table')
        
        # PPC_FORM
        if attributes_dictionary["PPC_FORM"] not in ['B', 'O', 'D', 'H', 'N'] and attributes_dictionary[
            "PPC_FORM"] != '':
            InvalidAttribute("PPC_FORM", attributes_dictionary["PPC_FORM"], not_applicable=False)

    elif class_type_str == "TCP":
        pass

    elif class_type_str == "PST":
        pass

    elif class_type_str == "CPS":
        # CPS_NAME
        PST_rows = session.query(schema.PST).all()  # gets the PST table
        PST_attributes = []
        for PST_object in PST_rows:
            PST_attributes.append(PST_object.PST_NAME)
        if attributes_dictionary["CPS_NAME"] not in PST_attributes:
            UnmatchingForeignKey('CPS_NAME', attributes_dictionary["CPS_NAME"], 'PST_NAME', 'PST_table')
        
        # CPS_PAR
        CDF_rows = session.query(schema.CDF).all()  # gets the CDF table
        CDF_attributes = []
        CSP_rows = session.query(schema.CSP).all()  # gets the CSP table
        CSP_attributes = []
        for CDF_object in CDF_rows:
            CDF_attributes.append(CDF_object.CDF_PNAME)
        for CSP_object in CSP_rows:
            CSP_attributes.append(CSP_object.CSP_NAME)
        if attributes_dictionary["CPS_PAR"] not in CDF_attributes and attributes_dictionary[
            "CPS_PAR"] not in CSP_attributes:
            UnmatchingForeignKey('CPS_PAR', attributes_dictionary["CPS_PAR"], 'CDF_PNAME/ CSP_NAME',
                                 'CDF_table/ CSP_table')
        
        # CPS_BIT
        if attributes_dictionary["CPS_PAR"] in CDF_attributes:
            CDF_rows = session.query(schema.CDF).all()  # gets the CDF table
            CDF_attributes = []
            for CDF_object in CDF_rows:
                CDF_attributes.append(CDF_object.CDF_BIT)
            if attributes_dictionary["CPS_BIT"] not in CDF_attributes:
                UnmatchingForeignKey('CPS_BIT', attributes_dictionary["CPS_BIT"], 'CDF_BIT', 'CDF_table')
        if attributes_dictionary["CPS_PAR"] in CSP_attributes:
            CSP_rows = session.query(schema.CSP).all()  # gets the CSP table
            CSP_attributes = []
            for CSP_object in CSP_rows:
                CSP_attributes.append(CSP_object.CSP_FPNUM)
            if attributes_dictionary["CPS_BIT"] not in CSP_attributes:
                UnmatchingForeignKey('CPS_BIT', attributes_dictionary["CPS_BIT"], 'CSP_FPNUM', 'CSP_table')

    object_updated = setDefaultValues(class_type_str, object_to_update)

    # Raise exceptions in recorded order
    if len(error_log) > 0:
        for exc in error_log:
            if override_attribute_dict[exc.field] == True:
                pass
            else:
                exc.raiseException()

    return object_updated


def setDefaultValues(class_type_str, object_to_update):
    """Sets default values (if they are left blank) and returns object updated."""
    if class_type_str == "DPF":
        pass

    elif class_type_str == "GPF":
        pass

    elif class_type_str == "TXF":
        pass

    elif class_type_str == "CAF":
        if object_to_update.CAF_INTER is None:
            object_to_update.CAF_INTER = 'F'

    elif class_type_str == "CAP":
        pass

    elif class_type_str == "PSV":
        pass

    elif class_type_str == "TXP":
        pass

    elif class_type_str == "CCF":
        if object_to_update.CCF_CRITICAL is None:
            object_to_update.CCF_CRITICAL = 'N'
        if object_to_update.CCF_PLAN is None:
            object_to_update.CCF_PLAN = 'N'
        if object_to_update.CCF_EXEC is None:
            object_to_update.CCF_EXEC = 'Y'
        if object_to_update.CCF_ILSCOPE is None:
            object_to_update.CCF_ILSCOPE = 'N'
        if object_to_update.CCF_ILSTAGE is None:
            object_to_update.CCF_ILSTAGE = 'C'
        if object_to_update.CCF_HIPRI is None:
            object_to_update.CCF_HIPRI = 'N'

    elif class_type_str == "CSF":
        if object_to_update.CSF_IFTT is None:
            object_to_update.CSF_IFTT = 'N'
        if object_to_update.CSF_CRITICAL is None:
            object_to_update.CSF_CRITICAL = 'N'
        if object_to_update.CSF_PLAN is None:
            object_to_update.CSF_PLAN = 'N'
        if object_to_update.CSF_EXEC is None:
            object_to_update.CSF_EXEC = 'Y'

    elif class_type_str == "CSS":
        if object_to_update.CSS_MANDISP is None:
            object_to_update.CSS_MANDISP = 'N'
        if object_to_update.CSS_RELTYPE is None:
            object_to_update.CSS_RELTYPE = 'R'
        if object_to_update.CSS_PREVREL is None:
            object_to_update.CSS_PREVREL = 'R'
        if object_to_update.CSS_DYNPTV is None:
            object_to_update.CSS_DYNPTV = 'N'
        if object_to_update.CSS_STAPTV is None:
            object_to_update.CSS_STAPTV = 'N'
        if object_to_update.CSS_CEV is None:
            object_to_update.CSS_CEV = 'N'

    elif class_type_str == "PAF":
        if object_to_update.PAF_RAWFMT is None:
            object_to_update.PAF_RAWFMT = 'U'

    elif class_type_str == "PAS":
        pass

    elif class_type_str == "DST":
        pass

    elif class_type_str == "PID":
        if object_to_update.PID_PI1_VAL is None:
            object_to_update.PID_PI1_VAL = 0
        if object_to_update.PID_PI2_VAL is None:
            object_to_update.PID_PI2_VAL = 0
        if object_to_update.PID_TPSD is None:
            object_to_update.PID_TPSD = -1
        if object_to_update.PID_TIME is None:
            object_to_update.PID_TIME = 'N'
        if object_to_update.PID_VALID is None:
            object_to_update.PID_VALID = 'Y'
        if object_to_update.PID_CHECK is None:
            object_to_update.PID_CHECK = 0
        if object_to_update.PID_EVENT is None:
            object_to_update.PID_EVENT = 'N'

    elif class_type_str == "CVS":
        if object_to_update.CVS_UNCERTAINTY is None:
            object_to_update.CVS_UNCERTAINTY = -1

    elif class_type_str == "VPD":
        if object_to_update.VPD_GRPSIZE is None:
            object_to_update.VPD_GRPSIZE = 0
        if object_to_update.VPD_FIXREP is None:
            object_to_update.VPD_FIXREP = 0
        if object_to_update.VPD_CHOICE is None:
            object_to_update.VPD_CHOICE = 'N'
        if object_to_update.VPD_PIDREF is None:
            object_to_update.VPD_PIDREF = 'N'
        if object_to_update.VPD_JUSTIFY is None:
            object_to_update.VPD_JUSTIFY = 'L'
        if object_to_update.VPD_NEWLINE is None:
            object_to_update.VPD_NEWLINE = 'N'
        if object_to_update.VPD_DCHAR is None:
            object_to_update.VPD_DCHAR = 0
        if object_to_update.VPD_FORM is None:
            object_to_update.VPD_FORM = 'N'
        if object_to_update.VPD_OFFSET is None:
            object_to_update.VPD_OFFSET = 0

    elif class_type_str == "PCF":
        if object_to_update.PCF_INTER is None:
            object_to_update.PCF_INTER = 'F'
        if object_to_update.PCF_USCON is None:
            object_to_update.PCF_USCON = 'N'
        if object_to_update.PCF_VALPAR is None:
            object_to_update.PCF_VALPAR = -1
        if object_to_update.PCF_CORR is None:
            object_to_update.PCF_CORR = 'Y'
        if object_to_update.PCF_DARC is None:
            object_to_update.PCF_DARC = '0'
        if object_to_update.PCF_ENDIAN is None:
            object_to_update.PCF_ENDIAN = 'B'

    elif class_type_str == "OCF":
        pass

    elif class_type_str == "OCP":
        if object_to_update.OCP_VALPAR is None:
            object_to_update.OCP_VALPAR = -1

    elif class_type_str == "GRP":
        pass

    elif class_type_str == "GRPA":
        pass

    elif class_type_str == "GRPK":
        pass

    elif class_type_str == "PLF":
        if object_to_update.PLF_NBOCC is None:
            object_to_update.PLF_NBOCC = -1
        if object_to_update.PLF_LGOCC is None:
            object_to_update.PLF_LGOCC = 0
        if object_to_update.PLF_TIME is None:
            object_to_update.PLF_TIME = 0
        if object_to_update.PLF_TDOCC is None:
            object_to_update.PLF_TDOCC = -1

    elif class_type_str == "TPCF":
        pass

    elif class_type_str == "SPF":
        pass

    elif class_type_str == "SPC":
        if object_to_update.SPC_UPDT is None:
            object_to_update.SPC_UPDT = ' '
        if object_to_update.SPC_MODE is None:
            object_to_update.SPC_MODE = ' '
        if object_to_update.SPC_FORM is None:
            object_to_update.SPC_FORM = 'N'
        if object_to_update.SPC_BACK is None:
            object_to_update.SPC_BACK = '0'

    elif class_type_str == "PCPC":
        if object_to_update.PCPC_CODE is None:
            object_to_update.PCPC_CODE = 'U'

    elif class_type_str == "PCDF":
        if object_to_update.PCDF_RADIX is None:
            object_to_update.PCDF_RADIX = 'H'

    elif class_type_str == "PSM":
        pass

    elif class_type_str == "PTV":
        if object_to_update.PTV_INTER is None:
            object_to_update.PTV_INTER = 'R'

    elif class_type_str == "GPC":
        if object_to_update.GPC_RAW is None:
            object_to_update.GPC_RAW = 'U'
        if object_to_update.GPC_SYMB0 is None:
            object_to_update.GPC_SYMB0 = '0'
        if object_to_update.GPC_LINE is None:
            object_to_update.GPC_LINE = '0'

    elif class_type_str == "CUR":
        pass

    elif class_type_str == "CVP":
        if object_to_update.CVP_TYPE is None:
            object_to_update.CVP_TYPE = 'C'

    elif class_type_str == "DPC":
        if object_to_update.DPC_COMM is None:
            object_to_update.DPC_COMM = 0
        if object_to_update.DPC_MODE is None:
            object_to_update.DPC_MODE = 'Y'
        if object_to_update.DPC_FORM is None:
            object_to_update.DPC_FORM = 'N'

    elif class_type_str == "CCA":
        if object_to_update.CCA_ENGFMT is None:
            object_to_update.CCA_ENGFMT = 'R'
        if object_to_update.CCA_RAWFMT is None:
            object_to_update.CCA_RAWFMT = 'U'
        if object_to_update.CCA_RADIX is None:
            object_to_update.CCA_RADIX = 'D'

    elif class_type_str == "CCS":
        pass

    elif class_type_str == "CPC":
        if object_to_update.CPC_DISPFMT is None:
            object_to_update.CPC_DISPFMT = 'R'
        if object_to_update.CPC_RADIX is None:
            object_to_update.CPC_RADIX = 'D'
        if object_to_update.CPC_CATEG is None:
            object_to_update.CPC_CATEG = 'N'
        if object_to_update.CPC_INTER is None:
            object_to_update.CPC_INTER = 'R'
        if object_to_update.CPC_CORR is None:
            object_to_update.CPC_CORR = 'Y'
        if object_to_update.CPC_OBTID is None:
            object_to_update.CPC_OBTID = 0
        if object_to_update.CPC_ENDIAN is None:
            object_to_update.CPC_ENDIAN = 'B'

    elif class_type_str == "CDF":
        if object_to_update.CDF_GRPSIZE is None:
            object_to_update.CDF_GRPSIZE = 0
        if object_to_update.CDF_INTER is None:
            object_to_update.CDF_INTER = 'R'

    elif class_type_str == "CVE":
        if object_to_update.CVE_INTER is None:
            object_to_update.CVE_INTER = 'R'
        if object_to_update.CVE_CHECK is None:
            object_to_update.CVE_CHECK = 'B'

    elif class_type_str == "PRF":
        if object_to_update.PRF_INTER is None:
            object_to_update.PRF_INTER = 'R'
        if object_to_update.PRF_DSPFMT is None:
            object_to_update.PRF_DSPFMT = 'U'
        if object_to_update.PRF_RADIX is None:
            object_to_update.PRF_RADIX = 'D'

    elif class_type_str == "PRV":
        pass

    elif class_type_str == "CSP":
        if object_to_update.CSP_DISPFMT is None:
            object_to_update.CSP_DISPFMT = 'R'
        if object_to_update.CSP_RADIX is None:
            object_to_update.CSP_RADIX = 'D'
        if object_to_update.CSP_CATEG is None:
            object_to_update.CSP_CATEG = 'N'

    elif class_type_str == "SDF":
        if object_to_update.SDF_FTYPE is None:
            object_to_update.SDF_FTYPE = 'E'

    elif class_type_str == "PVS":
        if object_to_update.PVS_INTER is None:
            object_to_update.PVS_INTER = 'R'

    elif class_type_str == "VDF":
        if object_to_update.VDF_RELEASE is None:
            object_to_update.VDF_RELEASE = 0
        if object_to_update.VDF_ISSUE is None:
            object_to_update.VDF_ISSUE = 0

    elif class_type_str == "MCF":
        if object_to_update.MCF_POL2 is None:
            object_to_update.MCF_POL2 = '0'
        if object_to_update.MCF_POL3 is None:
            object_to_update.MCF_POL3 = '0'
        if object_to_update.MCF_POL4 is None:
            object_to_update.MCF_POL4 = '0'
        if object_to_update.MCF_POL5 is None:
            object_to_update.MCF_POL5 = '0'

    elif class_type_str == "LGF":
        if object_to_update.LGF_POL2 is None:
            object_to_update.LGF_POL2 = '0'
        if object_to_update.LGF_POL3 is None:
            object_to_update.LGF_POL3 = '0'
        if object_to_update.LGF_POL4 is None:
            object_to_update.LGF_POL4 = '0'
        if object_to_update.LGF_POL5 is None:
            object_to_update.LGF_POL5 = '0'

    elif class_type_str == "PIC":
        if object_to_update.PIC_APID is None:
            object_to_update.PIC_APID = 99999

    elif class_type_str == "PPF":
        pass

    elif class_type_str == "PPC":
        if object_to_update.PPC_FORM is None:
            object_to_update.PPC_FORM = 'N'

    elif class_type_str == "TCP":
        pass

    elif class_type_str == "PST":
        pass

    elif class_type_str == "CPS":
        pass

    return object_to_update


def checkAppendixA(ptc, pfc):
    """Checks the validity of the ptc-pfc combination. Returns False if invalid."""
    valid = True
    if ptc == 1:
        if pfc != 0:
            valid = False
    elif ptc == 2:
        if pfc <= 0 or pfc >= 33:
            valid = False
    elif ptc == 3:
        if pfc < 0 or pfc > 16:
            valid = False
    elif ptc == 4:
        if pfc < 0 or pfc > 16:
            valid = False
    elif ptc == 5:
        if pfc < 1 or pfc > 4:
            valid = False
    elif ptc == 6:
        if pfc < 0 or pfc >= 33:
            valid = False
    elif ptc == 7:
        if pfc < 0:
            valid = False
    elif ptc == 8:
        if pfc < 0:
            valid = False
    elif ptc == 9:
        if pfc not in range(19):
            if pfc == 30:
                pass
            else:
                valid = False
    elif ptc == 10:
        if pfc < 3 or pfc > 18:
            valid = False
    elif ptc == 11:
        if pfc < 0:
            valid = False
    elif ptc == 12:
        pass
    elif ptc == 13:
        if pfc != 0:
            valid = False
    else:
        valid = False

    return valid


def setProgressBar(folder_path):
    """
    Output: 	0. total size of the table files in the specified directory.
                1. dictionary containing the size of each table file.
    """
    files = os.listdir(folder_path)
    size_dict = {}  # dictionary containing the size of each file
    total_size = 0
    for file_name in files:
        table = file_name.split('.')[0].upper()
        if table in schema.tablename_list and table not in schema.not_supported_tables:
            file_path = folder_path + "\\" + file_name
            file_size = os.path.getsize(file_path)
            size_dict.update({table: file_size})
            total_size += file_size

    return total_size, size_dict


def exportDatabaseAsDB(main_engine, main_session, location):
    """Saves database file (.db) at chose specified. Does not work."""
    # create new database
    backup_connection = sqlite3.connect(location + "\\backup_database.db")
    backup_engine = create_engine('sqlite:///' + location.replace('\\', '/') + '/backup_database.db', echo=False)
    schema.Base.metadata.create_all(backup_engine)
    backup_Session = sessionmaker(bind=backup_engine)
    backup_session = backup_Session()

    # fill database
    inspector = inspect(main_engine)
    for table_name in inspector.get_table_names():
        class_type_str = table_name.split('_table')[0]
        class_type = schema.tablename_dict[class_type_str]
        a = main_session.query(class_type).all()
        rows = a.copy()
        backup_session.bulk_save_objects(rows)
        backup_session.commit()

    backup_session.close()
    backup_engine.close()


def getColumnWidth(table_data, class_type):
    """Returns a dictionary with the maximum width of each column"""
    column_names = getColumnNames(class_type)[0]
    n_columns = len(column_names)

    # initialise dictionary
    max_width_dict = {}
    for i in range(n_columns):
        max_width_dict.update({i: len(column_names[i])})

    for i in range(len(table_data)):
        for j in range(n_columns):
            cell = str(table_data[i][j])
            if len(cell) > max_width_dict[j]:
                max_width_dict[j] = len(cell)

    return max_width_dict


def sortTableData(table_data, class_type):
    """
    sorts rows in table according to documentation.
         Input class_type as class.
    """
    try:
        if class_type == schema.VPD:
            column_names = getColumnNames(class_type)[0]
            vpd_tpsd_index = column_names.index('VPD_TPSD')
            vpd_pos_index = column_names.index('VPD_POS')

            sorted_table = sorted(table_data, key=itemgetter(vpd_tpsd_index, vpd_pos_index))
            return sorted_table
        elif class_type == schema.OCP:
            column_names = getColumnNames(class_type)[0]
            ocp_name_index = column_names.index('OCP_NAME')
            ocp_pos_index = column_names.index('OCP_POS')

            sorted_table = sorted(table_data, key=itemgetter(ocp_name_index, ocp_pos_index))
            return sorted_table
        elif class_type == schema.GPC:
            column_names = getColumnNames(class_type)[0]
            gpc_numbe_index = column_names.index('GPC_NUMBE')
            gpc_pos_index = column_names.index('GPC_POS')

            sorted_table = sorted(table_data, key=itemgetter(gpc_numbe_index, gpc_pos_index))
            return sorted_table
        elif class_type == schema.SPC:
            column_names = getColumnNames(class_type)[0]
            spc_numbe_index = column_names.index('SPC_NUMBE')
            spc_pos_index = column_names.index('SPC_POS')

            sorted_table = sorted(table_data, key=itemgetter(spc_numbe_index, spc_pos_index))
            return sorted_table
        else:
            return table_data
    except BaseException as exc:
        print("Unable to sort %s table. Error: %s" % (getClass(str(class_type)), str(exc)))
        return table_data


if __name__ == '__main__':
    pass
