#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  9 13:55:53 2021

@author: Clement
"""
import pandas
import geopandas as gpd
import numpy
import os
import sys
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import file_fct
from gen_fct import df_fct

def last_update_db (dir_name, db_list):
    list_dir, list_files = file_fct.list_dir_files(f'{dir_name}')
    db_daily = db_list[db_list.loc[:,'update']==True]
    
    if 'last_update.json' in list_files:
        last_update = pandas.read_json(f'{dir_name}/last_update.json', orient = "table")
        last_update['delta_day'] = last_update.apply(lambda x: (pandas.to_datetime('today')-x["date"]).days,axis=1)
        print(last_update)
        print('\n')
    else:
        last_update = pandas.DataFrame(index=db_daily.index, columns=['date', 'delta_day'])
        last_update.loc[:,'delta_day'] = 100 #Arbitrary value
        
    return last_update

def import_and_save(df_name, root, source_df):
    save_path = os.path.normcase(f'{root}{source_df.loc[df_name, "sub_dir"]}/{source_df.loc[df_name, "file_name"]}')
    file_fct.creation_folder(root,[source_df.loc[df_name, "sub_dir"]])
    
    if source_df.loc[df_name, 'type'] == 'Pandas':
        importing_df = pandas.read_csv(source_df.loc[df_name, 'link'], 
                                       sep=source_df.loc[df_name, 'sep'],
                                       encoding=source_df.loc[df_name, 'encoding'])
        
        importing_df.to_csv(save_path, index=False, sep=source_df.loc[df_name, 'sep'])
        
        
    elif source_df.loc[df_name, 'type'] == 'GeoPandas':
        importing_df = gpd.read_file(source_df.loc[df_name, 'link'])
        importing_df.to_file(save_path, index=False)
        
    return importing_df

def import_static (data_dir, db_list):
    raw_data_dir = os.path.normcase(f'{data_dir}/raw')
    list_dir, list_files = file_fct.list_dir_files(raw_data_dir)
    df_static = db_list[db_list.loc[:,'update']==False]
   
    for a_df_name in df_static.index:
        if df_static.loc[a_df_name, 'file_name'] not in list_files:
            print(f"Downloading {df_static.loc[a_df_name, 'file_name']}...", end='\x1b[1K\r')
            import_and_save(a_df_name, raw_data_dir, df_static)
            print(f"{df_static.loc[a_df_name, 'file_name']} downloaded")
    print('\n\n')

def import_daily (data_dir, db_list, last_update_db, limit):
    raw_data_dir = os.path.normcase(f'{data_dir}/raw')
    df_daily = db_list[db_list.loc[:,'update']==True]
    
    for a_df_name in df_daily.index:
        if a_df_name not in last_update_db.index:
            print(f"Creating and downloading {df_daily.loc[a_df_name, 'file_name']}...", end='')
            df = import_and_save(a_df_name, raw_data_dir, df_daily)
            delta_spaces = " "*(len(f"Creating and downloading {df_daily.loc[a_df_name, 'file_name']}...")-len(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded"))
            print(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded {delta_spaces}")
            
            last_update = get_dates (df, a_df_name, db_list)
            last_update_db.loc[a_df_name, 'date'] = last_update
            
        elif last_update_db.loc[a_df_name, 'delta_day'] > limit:
            print(f"Downloading {df_daily.loc[a_df_name, 'file_name']}...", end='')
            df = import_and_save(a_df_name, raw_data_dir, df_daily)
            delta_spaces = " "*(len(f"Downloading {df_daily.loc[a_df_name, 'file_name']}...")-len(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded"))
            print(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded {delta_spaces}")
            
            last_update = get_dates (df, a_df_name, db_list)
            last_update_db.loc[a_df_name, 'date'] = last_update
        
    data_dir = file_fct.get_parent_dir(2, 'data')
    last_update_db['delta_day'] = last_update_db.apply(lambda x: (pandas.to_datetime('today')-x["date"]).days,axis=1)
    print(last_update_db)
    last_update_db.loc[:,'date'] = last_update_db.apply(lambda x: x["date"].strftime("%Y-%m-%d"), axis=1)
    last_update_db.to_json(f'{data_dir}/last_update.json', orient = "table", indent=4)
              
    print('\n\n')
    
def get_dates (df, df_name, db_list):
    db_list = db_list.fillna('')
    
    if db_list.loc[df_name, 'drop_col'] != '':
        df = df.drop(columns=db_list.loc[df_name, 'drop_col'].split(','))
    
    if db_list.loc[df_name, 'id_vars'] != '':
        df = pandas.melt(df, id_vars=db_list.loc[df_name, 'id_vars'].split(','), var_name=db_list.loc[df_name, 'index_name'])
    df = df.set_index(db_list.loc[df_name, 'index_name'])
        
    if db_list.loc[df_name, 'drop_val'] != '':
        df = df.drop(index=db_list.loc[df_name, 'drop_val'].split(','))
    
    if db_list.loc[df_name, 'date_format'] != '':
        df.index = pandas.to_datetime(df.index, format=db_list.loc[df_name, 'date_format'])
    else:
        df.index = pandas.to_datetime(df.index)
    df = df.sort_index()
        
    last_update = df.index[-1] + datetime.timedelta(days=db_list.loc[df_name, 'time_delta'])
    return last_update


def force_download(data_dir, db_list, last_update, update_limit):
    print('** Entering force downloading mode **')
    raw_data_dir = os.path.normcase(f'{data_dir}/raw')
    df_daily = db_list[db_list.loc[:,'update']==True]
    
    for a_df_name in df_daily.index:
        print(f"Creating and downloading {df_daily.loc[a_df_name, 'file_name']}...", end='')
        import_and_save(a_df_name, raw_data_dir, df_daily)
        delta_spaces = " "*(len(f"Creating and downloading {df_daily.loc[a_df_name, 'file_name']}...")-len(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded"))
        print(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded {delta_spaces}")
            
        
    print('\n\n')

def main(update_limit):
    
    data_dir = file_fct.get_parent_dir(2, 'data') # .../COVID19/data
    db_list = df_fct.read_db_list ('raw')
    last_update = last_update_db (data_dir, db_list)
    
    import_static (data_dir, db_list)
    import_daily (data_dir, db_list, last_update, update_limit)
    #force_download(data_dir, db_list, last_update, update_limit)


if __name__ == '__main__':
    main(1)
    """
    db_list = df_fct.read_db_list ('raw')
    
    db_list.loc["World_JH_cases", 'index_name'] = 'date'
    db_list.loc["World_JH_cases", 'data_format'] = ''
    db_list.loc["World_JH_cases", 'drop_col'] = 'Province/State,Lat,Long'
    db_list.loc["World_JH_cases", 'drop_val'] = ''
    db_list.loc["World_JH_cases", 'time_delta'] = 2
    db_list.loc["World_JH_cases", 'id_vars'] = 'Country/Region'
    
    data_dir = file_fct.get_parent_dir(2, 'data')
    db_list.to_json(f'{data_dir}/list_raw_data.json', orient = "table", indent=4)
    """
