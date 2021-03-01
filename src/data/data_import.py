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
                                       encoding=source_df.loc[df_name, 'encoding'],
                                       dtype='object')
        importing_df.to_csv(save_path, index=False, sep=source_df.loc[df_name, 'sep'])
        
    elif source_df.loc[df_name, 'type'] == 'GeoPandas':
        importing_df = gpd.read_file(source_df.loc[df_name, 'link'])
        importing_df.to_file(save_path, index=False)

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
        if last_update_db.loc[a_df_name, 'delta_day'] > limit:
            print(f"Downloading {df_daily.loc[a_df_name, 'file_name']}...", end='')
            import_and_save(a_df_name, raw_data_dir, df_daily)
            print(f"\r{df_daily.loc[a_df_name, 'file_name']} was downloaded")
    print('\n\n')

def get_dates (data_dir, db_list, last_update):
    group1 = ["World_JH_cases", "World_JH_death", "US_JH_cases", "US_JH_death"]
    
    for df_name in  group1:
        path = os.path.normcase(f'{data_dir}/raw{db_list.loc[df_name, "sub_dir"]}/{db_list.loc[df_name, "file_name"]}')
        df = pandas.read_csv(path)
        date = pandas.to_datetime(df.columns[-1])
        last_update.loc[df_name, 'date'] = date
    
    path = os.path.normcase(f'{data_dir}/raw{db_list.loc["US_Testing", "sub_dir"]}/{db_list.loc["US_Testing", "file_name"]}')
    df = pandas.read_csv(path)
    df.loc[:,'date'] = pandas.to_datetime(df.loc[:,'date'], format='%Y%m%d')
    df = df.set_index('date').sort_index()
    last_update.loc["US_Testing", 'date'] = df.index[-1]
    
    path = os.path.normcase(f'{data_dir}/raw{db_list.loc["Fra_GenData", "sub_dir"]}/{db_list.loc["Fra_GenData", "file_name"]}')
    df = pandas.read_csv(path, dtype={'source_url': str, 'source_archive': str}).set_index('date').drop(index=['2020-11_11'])
    df.index = pandas.to_datetime(df.index, format='%Y-%m-%d')
    df = df.sort_index()
    last_update.loc["Fra_GenData", 'date'] = df.index[-1]
    
    path = os.path.normcase(f'{data_dir}/raw{db_list.loc["Fra_Indic_Nat", "sub_dir"]}/{db_list.loc["Fra_Indic_Nat", "file_name"]}')
    df = pandas.read_csv(path).set_index('extract_date')
    df.index = pandas.to_datetime(df.index, format='%Y-%m-%d')
    df = df.sort_index()
    last_update.loc["Fra_Indic_Nat", 'date'] = df.index[-1]
    
    path = os.path.normcase(f'{data_dir}/raw{db_list.loc["Fra_Indic_Dpt", "sub_dir"]}/{db_list.loc["Fra_Indic_Dpt", "file_name"]}')
    df = pandas.read_csv(path).set_index('extract_date')
    df.index = pandas.to_datetime(df.index, format='%Y-%m-%d')
    df = df.sort_index()
    last_update.loc["Fra_Indic_Dpt", 'date'] = df.index[-1]
    
    path = os.path.normcase(f'{data_dir}/raw{db_list.loc["Fra_Testing2", "sub_dir"]}/{db_list.loc["Fra_Testing2", "file_name"]}')
    df = pandas.read_csv(path, sep=';')
    print(df)
    df = df.set_index('jour')
    df.index = pandas.to_datetime(df.index, format='%Y-%m-%d')
    df = df.sort_index()
    last_update.loc["Fra_Testing2", 'date'] = df.index[-1]+datetime.timedelta(days=2)
    last_update.loc["Fra_Testing1", 'date'] = df.index[-1]+datetime.timedelta(days=2)
    
    path = os.path.normcase(f'{data_dir}/raw{db_list.loc["Fra_Vax", "sub_dir"]}/{db_list.loc["Fra_Vax", "file_name"]}')
    df = pandas.read_csv(path).set_index('jour')
    df.index = pandas.to_datetime(df.index, format='%Y-%m-%d')
    df = df.sort_index()
    last_update.loc["Fra_Vax", 'date'] = df.index[-1]
    
    last_update['delta_day'] = last_update.apply(lambda x: (pandas.to_datetime('today')-x["date"]).days,axis=1)
    print(last_update)
    last_update.loc[:,'date'] = last_update.apply(lambda x: x["date"].strftime("%Y-%m-%d"), axis=1)
    last_update.to_json(f'{data_dir}/last_update.json', orient = "table", indent=4)

def main(update_limit):
    data_dir = file_fct.get_parent_dir(2, 'data') # .../COVID19/data
    db_list = df_fct.read_db_list ('raw')
    last_update = last_update_db (data_dir, db_list)
    
    import_static (data_dir, db_list)
    import_daily (data_dir, db_list, last_update, update_limit)
    
    get_dates (data_dir, db_list, last_update)


if __name__ == '__main__':
    main(1)

