import os 
import numpy
import pandas

def read_db_list ():
    data_dir = get_parent_dir(2, 'data')
    db_list_path = os.path.normcase(f'{dir_name}/data.json')
    db_list = pandas.read_json(db_list_path, orient = "table")
    return db_list

def import_df (list_df, list_prop):
    db_list = read_db_list (data_dir)
    data_dir = get_parent_dir(2, 'data')

    list_df = []
    for a_df, a_prop in zip(list_df, list_prop):
        if a_prop == 'raw':
            import_path = os.path.normcase(f'{data_dir}/raw/{source_df.loc[df_name, "sub_dir"]}/{source_df.loc[df_name, "file_name"]}')
            df = pandas.read_csv(import_path, 
                                       sep=source_df.loc[df_name, 'sep'],
                                       encoding=source_df.loc[df_name, 'encoding'],
                                       dtype='object')

        elif a_prop == 'processed':
            import_path = os.path.normcase(f'{data_dir}/processed/{source_df.loc[df_name, "sub_dir"]}/{source_df.loc[df_name, "file_name"]}')

            try:
                df = pandas.read_csv(import_path, 
                                       sep=source_df.loc[df_name, 'sep'],
                                       encoding=source_df.loc[df_name, 'encoding'],
                                       dtype='object')
            except FileNotFoundError:
                import_path = os.path.normcase(f'{data_dir}/raw/{source_df.loc[df_name, "sub_dir"]}/{source_df.loc[df_name, "file_name"]}')
                df = pandas.read_csv(import_path, 
                                       sep=source_df.loc[df_name, 'sep'],
                                       encoding=source_df.loc[df_name, 'encoding'],
                                       dtype='object')
                print('{a_df} not found, imported raw data')

        else:
            raise Warning("Data frame prop must be 'raw' or 'processed'")

        list_df.append(df)

    return list_df