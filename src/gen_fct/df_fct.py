#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  10 13:25:01 2021

@author: Clement
"""

import os 
import numpy
import pandas
#%%
import geopandas as gpd
#%%
from gen_fct import file_fct

def read_db_list (type):
    data_dir = file_fct.get_parent_dir(2, 'data')
    if type =='raw':
        db_list_path = os.path.normcase(f'{data_dir}/list_raw_data.json')
    elif type == 'processed':
        db_list_path = os.path.normcase(f'{data_dir}/list_processed_data.json')

    db_list = pandas.read_json(db_list_path, orient = "table")
    return db_list

def import_df (list_df, list_prop):
    data_dir = file_fct.get_parent_dir(2, 'data')
    
    list_final_df = []
    for df_name, a_prop in zip(list_df, list_prop):
        source_df = read_db_list (a_prop)
        import_path = os.path.normcase(f'{data_dir}/{a_prop}/{source_df.loc[df_name, "sub_dir"]}/{source_df.loc[df_name, "file_name"]}')
        export_format = source_df.loc[df_name, "file_name"].split('.')[-1]
        if source_df.loc[df_name, 'type'] == 'Pandas':
            if export_format == 'csv':
                importing_df = pandas.read_csv(import_path, 
                                             sep=source_df.loc[df_name, 'sep'],
                                             encoding=source_df.loc[df_name, 'encoding'])
            elif export_format == 'json':
                importing_df = pandas.read_json(import_path, orient = "table")
                
        elif source_df.loc[df_name, 'type'] == 'GeoPandas':
            if export_format == 'csv' or export_format == 'shp':
                importing_df = gpd.read_file(import_path)
            elif export_format == 'json' or export_format == 'geojson':
                importing_df = gpd.read_json(import_path, orient = "table")
            elif export_format == 'feather':
                importing_df = gpd.read_feather(import_path)
                
      
        list_final_df.append(importing_df)
        print(df_name)
        print(importing_df)

    return list_final_df

def export_df (list_df, list_prop): #list_df = [['name', df], ..., ], list_prop = [processed, raw]
    data_dir = file_fct.get_parent_dir(2, 'data')

    list_final_df = []
    for df_prop, a_prop in zip(list_df, list_prop):
        df_name, df = df_prop
        source_df = read_db_list (a_prop)
        file_path = file_fct.creation_folder(f'{data_dir}/{a_prop}', [f'{source_df.loc[df_name, "sub_dir"]}'])
        export_path = f'{file_path[0]}/{source_df.loc[df_name, "file_name"]}'
        export_format = source_df.loc[df_name, "file_name"].split('.')[-1]
        if source_df.loc[df_name, 'type'] == 'Pandas':
            if export_format == 'csv':
                df.to_csv(export_path, index=True)
            elif export_format == 'json':
                df.to_json(export_path, orient = "table", indent=4)
            else:
                print(f"File {source_df.loc[df_name, 'file_name']} couldn't be saved, please change extension")


        elif source_df.loc[df_name, 'type'] == 'GeoPandas':
            if export_format == 'shp':
                df.to_file(export_path, index=True)
            elif export_format == 'geojson':
                df.to_file(export_path, orient = "table", indent=4, driver="GeoJSON")
            elif export_format == 'feather':
                df.to_feather(export_path)
            else:
                print(f"File {source_df.loc[df_name, 'file_name']} couldn't be saved, please change extension")

    return list_final_df

def read_db_files ():
    data_dir = file_fct.get_parent_dir(2, 'data')
    db_file = pandas.read_json(f'{data_dir}/list_files.json', orient = "table")
    db_file_date = pandas.read_json(f'{data_dir}/list_files_date.json', orient = "table")

    return db_file, db_file_date

def save_db_files (db_file, db_file_date):
    data_dir = file_fct.get_parent_dir(2, 'data')

    db_file.to_json(f'{data_dir}/list_files.json', orient = "table", indent=4)
    db_file_date.to_json(f'{data_dir}/list_files_date.json', orient = "table", indent=4)


def write_db_files (file, date, files_para):
    db_file, db_file_date = read_db_files ()

    if files_para.get('file', file) not in db_file.index:
        db_file.loc[files_para.get('file', file)] = [files_para['local_path'], files_para['local_path_prev'], files_para['ftp_path'],
                                                     files_para['pref'], files_para['suf'],
                                                     files_para['add_date'], files_para['type_file']]

    db_file_date.loc[files_para.get('file', file), 'date'] = files_para.get('date', date)

    return db_file, db_file_date



if __name__ == '__main__':
    db_file, db_file_date = read_db_files ()
    
    
    
    
    
    
    