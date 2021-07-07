tryout_location= "C:\\Users\\andres.miguelez\\Documents\\prueba_leer.xlsx"
real_location= r'.\Field description'

import pandas as pd
import numpy as np
import schema

# create data dictionary
data_info_dict= {}
for table in schema.tablename_list:
    data_info_dict.update({table : {}})

data = pd.read_excel (real_location + r"\MOC.xlsx")

currently_in_table = True # indicates a different class than the previous row

for index, row in data.iterrows():
    row_as_list= list(row)
    if str(row_as_list[0]) != 'nan' and str(row_as_list[1]) != 'nan': # rows that actually have content
        field_name= str(row_as_list[0])
        field_description= str(row_as_list[1])

        # if field_name == 'CUR_SELECT':
        #     print("Stop")

        class_type_str= field_name.split('_')[0]
        
        if class_type_str in schema.tablename_list:
            data_info_dict[class_type_str].update({field_name : field_description})


# print onto files
error_log = []
# for table, table_attributes in data_info_dict.items():
#     arc= open(real_location + '\\files\\' + table + '_description.txt', 'w')
#     for field_name, field_description in table_attributes.items():
#         try:
#             arc.write("%s: \t%s'end_of_field'" % (field_name, field_description))
#         except BaseException as exc:
#             error_log.append(exc)
#             print(field_name)
#     else:
#         arc.close()

if __name__== '__main__':
    print("error count: %d" % len(error_log))
