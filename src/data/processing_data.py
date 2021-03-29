#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 11 18:29:39 2021

@author: Clement
"""
import pandas
import numpy
import os
import sys
import geopandas as gpd
import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import df_fct
from gen_fct import file_fct

class WorldDataSet:
    def __init__ (self):
        self.df_cases = pandas.DataFrame()
        self.df_death = pandas.DataFrame()
        self.df_fra = pandas.DataFrame()
        self.df_world = pandas.DataFrame()
        self.df_fra_backup = pandas.DataFrame()
    
    def import_db(self):
        self.df_cases, self.df_death = df_fct.import_df(['World_JH_cases', 'World_JH_death'],
                                                                     ['raw' for x in range(2)])
        self.df_fra = df_fct.import_df(['Fra_Nat'], ['processed'])[0]
        
    
    def clean_up_JH (self):
        list_df = [self.df_cases, self.df_death]
        name_df = ['cases', 'death']

        list_return = []
        for a_df, a_name in zip(list_df, name_df):
            a_df = a_df.drop(['Lat', 'Long'], axis=1)
            a_df = a_df.groupby("Country/Region").sum()
            a_df.loc['World'] = a_df.sum()
            a_df = pandas.melt(a_df.reset_index(), id_vars=["Country/Region"], value_vars=a_df.columns, var_name='date', value_name=a_name)
            a_df.loc[:,"date"] = pandas.to_datetime(a_df.loc[:,"date"])
            a_df = a_df.replace('Korea, South', 'South Korea')
            a_df = a_df.set_index(['Country/Region', 'date'])
            a_df.index = a_df.index.rename(['country', 'date'])
            list_return.append(a_df)
            
        self.df_world = pandas.concat(list_return, axis=1).sort_index()

    def ajust_values (self):
        ini_date = pandas.to_datetime('2020-04-03', format='%Y-%m-%d')
        last_date_world = self.df_world.index.get_level_values(1).unique('date')[-1]
        last_date_fra = self.df_fra.index[-1]
        if last_date_world <= last_date_fra:
            self.df_world.loc[('France', ini_date): ('France', last_date_world), 'cases'] = self.df_fra.loc[ini_date: last_date_world, ['cases']].values

        elif last_date_world > last_date_fra:
            raise ValueError(f'Source data and fra data ({last_date_fra.strftime("%d-%m-%Y")}) not aligned')
        
        self.df_world.loc['World'] = self.df_world.sum(level='date').values
    

    def complete_data (self):
        for type_data in ['cases', 'death']:
            self.df_world.loc[:,f'delta_{type_data}'] = self.df_world.loc[:,type_data].groupby(level='country').diff()
            self.df_world.loc[:,f'growth_{type_data}'] = self.df_world.loc[:,type_data].groupby(level='country').pct_change()*100
            self.df_world.loc[:,f'weekly_growth_{type_data}'] = self.df_world.loc[:,type_data].groupby(level='country').pct_change(periods=7)
        
        self.df_world.loc[:,'fatality_rate'] = self.df_world.loc[:,'cases'].div(self.df_world.loc[:,'death'])
        self.df_world.loc[:,'fatality_rate'] = self.df_world.loc[:,'fatality_rate']/10
    
    def smooth (self, period, center):
        self.df_world = self.df_world.rolling(window = period, center=center).mean()
            
    def main(self, period, center):
        self.import_db()
        self.clean_up_JH ()
        #self.clean_up_Fra_gen ()
        self.ajust_values ()
        self.complete_data ()
        self.smooth (period, center)
        df_fct.export_df([['World_JH', self.df_world]], ['processed'])
        
        return self.df_world

class FrenchDataSets:
    def __init__ (self):
        self.df_fra, self.df_fra_backup = df_fct.import_df(['Fra_GenData', 'Fra_Backup'],['raw', 'raw'])
        self.df_dpt_shp = df_fct.import_df(['Fra_Departements_shapefile'],['raw'])[0]
        self.df_fra_nat = pandas.DataFrame()
        self.df_fra_reg = pandas.DataFrame()
        self.df_fra_dpt = pandas.DataFrame()
        
    def clean_up_nat (self):
        self.df_fra_backup = self.df_fra_backup.set_index('date')
        self.df_fra_backup.loc[:,'cases'] = pandas.to_numeric(self.df_fra_backup.loc[:,'cases'], downcast='float')
        self.df_fra_backup.index = pandas.to_datetime(self.df_fra_backup.index)
        
        self.df_fra = self.df_fra.set_index('date')
        self.df_fra = self.df_fra.drop(index=['2020-11_11']).reset_index()
        
        df_sort_1 = self.df_fra[(self.df_fra.loc[:,'granularite']=='pays') & (self.df_fra.loc[:,'source_type']=='opencovid19-fr')]
        df_sort_2 = self.df_fra[(self.df_fra.loc[:,'granularite']=='pays') & (self.df_fra.loc[:,'source_type']=='ministere-sante')]
        
        if df_sort_1.index[-1] <= df_sort_2.index[-1]:
            self.df_fra_nat = df_sort_2.set_index('date')
            self.df_fra_nat.index = pandas.to_datetime(self.df_fra_nat.index, format='%Y-%m-%d')
            self.df_fra_nat = self.df_fra_nat.sort_index()
            self.df_fra_nat['deces_ehpad'] = self.df_fra_nat['deces_ehpad'].fillna(method='ffill').fillna(0)
            self.df_fra_nat.loc[:,'deces'] = self.df_fra_nat.loc[:,'deces'] + self.df_fra_nat.loc[:,'deces_ehpad']
            self.df_fra_nat = self.df_fra_nat.loc[:, ['cas_confirmes', 'deces', 'reanimation', 'hospitalises']]
            self.df_fra_nat = self.df_fra_nat.rename(columns={'cas_confirmes':'cases', 'deces':'death'})
            self.update_backup()
            
        else:
            self.df_fra_nat = df_sort_1.set_index('date')
            self.df_fra_nat.index = pandas.to_datetime(self.df_fra_nat.index, format='%Y-%m-%d')
            self.df_fra_nat = self.df_fra_nat.sort_index()
            self.df_fra_nat = self.df_fra_nat.loc[:, ['cas_confirmes', 'deces', 'reanimation', 'hospitalises']]
            self.df_fra_nat = self.df_fra_nat.rename(columns={'cas_confirmes':'cases', 'deces':'death'})
            
            if self.df_fra_backup.index[-1] < self.df_fra_nat.index[-1]:
                raise ValueError(f'Source data and backup data for France ({self.df_fra_backup.index[-1].strftime("%d-%m-%Y")}) not available')
            
            else:
                print('Using backup data')
                self.df_fra_nat.loc[self.df_fra_nat.index[0]:self.df_fra_nat.index[-1], ['cases']] = self.df_fra_backup.loc[self.df_fra_nat.index[0]:self.df_fra_nat.index[-1], ['cases']].values
        
        for type_data in ['cases', 'death']:
            self.df_fra_nat.loc[:,f'delta_{type_data}'] = self.df_fra_nat.loc[:,type_data].diff()
            self.df_fra_nat.loc[:,f'growth_{type_data}'] = self.df_fra_nat.loc[:,type_data].pct_change()
            self.df_fra_nat.loc[:,f'weekly_growth_{type_data}'] = self.df_fra_nat.loc[:,type_data].pct_change(periods=7)
    
    def update_backup(self):
        day_after = self.df_fra_backup.index[-1] + pandas.Timedelta(1, unit='d')
        self.df_fra_backup = pandas.concat([self.df_fra_backup.loc[:,['cases']], self.df_fra_nat.loc[day_after:,['cases']]]) 
        
    def clean_up_reg (self):
        self.df_fra_reg = self.df_fra[(self.df_fra.loc[:,'granularite']=='region') & (self.df_fra.loc[:,'source_type']=='opencovid19-fr')]
        self.df_fra_reg.loc[:,'date'] = pandas.to_datetime(self.df_fra_reg.loc[:,'date'], format='%Y-%m-%d')
        self.df_fra_reg = self.df_fra_reg.set_index(['maille_nom', 'date']).sort_index()
        self.df_fra_reg.index = self.df_fra_reg.index.rename(['region', 'date'])
        self.df_fra_reg = self.df_fra_reg.loc[:,['deces']]
        self.df_fra_reg = self.df_fra_reg.rename(columns={'deces':'death'})
        self.df_fra_reg = self.add_para ('df_fra_reg', 'region')
        
    def clean_up_dpt (self):    
        self.df_fra_dpt = self.df_fra[(self.df_fra.loc[:,'granularite']=='departement') & (self.df_fra.loc[:,'source_type']=='sante-publique-france-data')]
        self.df_fra_dpt.loc[:,'date'] = pandas.to_datetime(self.df_fra_dpt.loc[:,'date'], format='%Y-%m-%d')
        self.df_fra_dpt.loc[:,'maille_code'] = self.df_fra_dpt.loc[:,'maille_code'].apply(lambda dpt: dpt[4:])
        self.df_fra_dpt = self.df_fra_dpt.set_index(['maille_nom', 'date']).sort_index()
        self.df_fra_dpt.index = self.df_fra_dpt.index.rename(['departement', 'date'])
        self.df_fra_dpt = self.df_fra_dpt.loc[:,['deces', 'reanimation', 'hospitalises']]
        self.df_fra_dpt = self.df_fra_dpt.rename(columns={'deces':'death'})
        self.df_fra_dpt = self.add_para ('df_fra_dpt', 'departement')
        
    def add_para (self, df, level):
        df = getattr(self, df)
        for type_data in ['death']:
            df.loc[:,f'delta_{type_data}'] = df.loc[:,type_data].groupby(level=level).diff()
            df.loc[:,f'growth_{type_data}'] = df.loc[:,type_data].groupby(level=level).pct_change()
            df.loc[:,f'weekly_growth_{type_data}'] = df.loc[:,type_data].groupby(level=level).pct_change(periods=7)
        
        return df
    
    def main (self):
        self.clean_up_nat()
        self.clean_up_reg()
        self.clean_up_dpt()
        
        df_fct.export_df([['Fra_Nat', self.df_fra_nat], ['Fra_Reg', self.df_fra_reg], ['Fra_Dpt', self.df_fra_dpt], ['Fra_Backup', self.df_fra_backup]],
                         ['processed', 'processed', 'processed', 'processed'])


class FrenchIndic ():
    def __init__ (self):
        self.df_indic_nat = df_fct.import_df(['Fra_Indic_Nat'],['raw'])[0]
        self.df_indic_dpt = df_fct.import_df(['Fra_Indic_Dpt'],['raw'])[0]
        self.df_dpt_shp = df_fct.import_df(['Fra_Departements_shapefile'],['raw'])[0]

    def indic_nat (self):
        self.df_indic_nat = self.df_indic_nat.set_index('extract_date')
        self.df_indic_nat.index = pandas.to_datetime(self.df_indic_nat.index, format='%Y-%m-%d')
        self.df_indic_nat.index = self.df_indic_nat.index.rename('date')
        
    def indic_dpt(self):
        self.df_indic_dpt.loc[:,'extract_date'] = pandas.to_datetime(self.df_indic_dpt.loc[:,'extract_date'], format='%Y-%m-%d')
        self.df_indic_dpt = self.df_indic_dpt.set_index(['extract_date', 'departement'])

        self.df_dpt_shp = self.df_dpt_shp.set_index('code')
        self.df_dpt_shp.index = self.df_dpt_shp.index.rename('departement')
        
        self.df_indic_dpt = self.df_indic_dpt.sort_index(level='extract_date')
        self.df_indic_dpt = self.df_indic_dpt.sort_index(level='departement')
        self.df_indic_dpt = self.df_indic_dpt.fillna(method='ffill')
        
        self.df_indic_dpt_graph = self.df_indic_dpt.swaplevel().sort_index()
        self.df_indic_dpt_graph = self.df_indic_dpt_graph.drop(columns=['tx_incid_couleur', 'R_couleur', 
                                                                        'taux_occupation_sae_couleur', 'tx_pos_couleur', 'nb_orange', 'nb_rouge'])
        
        self.df_indic_dpt_map = self.df_indic_dpt.join(self.df_dpt_shp)
        self.df_indic_dpt_map = gpd.GeoDataFrame(self.df_indic_dpt_map)
        self.df_indic_dpt_map = self.df_indic_dpt_map.dropna(subset=['nom'])
        self.df_indic_dpt_map = self.df_indic_dpt_map.sort_index(level='extract_date')

    def main(self):
        self.indic_nat ()
        self.indic_dpt()

        df_fct.export_df([['Fra_Indic_Nat', self.df_indic_nat], ['Fra_Indic_Dpt_graph', self.df_indic_dpt_graph]],
                         ['processed', 'processed'])

        return self.df_indic_dpt_map


class FrenchVax ():
    def __init__(self):
        self.data_vax = df_fct.import_df(['Fra_Vax'],['raw'])[0]
        
    def clean_up_vax (self):
        self.data_vax.loc[:,'date'] = pandas.to_datetime(self.data_vax.loc[:,'jour'])
        self.data_vax = self.data_vax.drop(columns=['jour'])
        self.data_vax = self.data_vax.set_index(['date'])
        self.data_vax = self.data_vax.rename(columns={'n_dose1': 'vaccin jour', 'n_cum_dose1':'total_vaccines'})
        self.data_vax.loc[:,'vaccin jour'] = self.data_vax.loc[:,'vaccin jour'].rolling(window=7, center=False).mean() 
        
        dv = self.data_vax.loc[self.data_vax.index[-1],'total_vaccines'] - self.data_vax.loc[self.data_vax.index[0], 'total_vaccines']
        dt = (self.data_vax.index[-1] - self.data_vax.index[0]).days
        dvdt = dv/dt
        
        for date in self.data_vax.index:
            jour = (date - self.data_vax.index[0]).days
            self.data_vax.loc[date, 'vax journalier'] = dvdt*jour + self.data_vax.loc[self.data_vax.index[0], 'total_vaccines']
        
        days_to_targ = int(0.6 * 66 * 10**6 / dvdt)
        date_to_targ = self.data_vax.index[-1] + pandas.Timedelta(days_to_targ, unit='d')
        self.data_vax.loc[date_to_targ, 'vax journalier'] = 0.6 * 66 * 10**6
        print(self.data_vax.loc[date_to_targ])
        
        print(self.data_vax)
        return self.data_vax
    
    def main(self):
        self.clean_up_vax()
        df_fct.export_df([['Fra_Vax', self.data_vax]],
                          ['processed'])

        
        return self.data_vax
        

class FrenchTest ():
    def __init__(self):
        self.fra_testing_1, self.fra_testing_2 = df_fct.import_df(['Fra_Testing1', 'Fra_Testing2'],
                                                                  ['raw', 'raw'])
        self.fra_testing = pandas.DataFrame()
    
    def clean_up_testing_1 (self):
        self.fra_testing_1.loc[:, 'jour'] = pandas.to_datetime(self.fra_testing_1.loc[:, 'jour'], format='%Y-%m-%d')
        self.fra_testing_1 = self.fra_testing_1[self.fra_testing_1.loc[:,'clage_covid']=='0']
        self.fra_testing_1 = self.fra_testing_1.groupby('jour').sum()
        self.fra_testing_1 = self.fra_testing_1.rename(columns={'nb_test': 'Daily tests', 'nb_pos': 'Daily positive'})
        self.fra_testing_1 = self.fra_testing_1.loc[:, ['Daily tests', 'Daily positive']]
        self.fra_testing_1.loc[:,'Daily positive rate'] = self.fra_testing_1.loc[:,'Daily positive'].div(self.fra_testing_1.loc[:,'Daily tests'])
        self.fra_testing_1 = self.fra_testing_1.loc[:pandas.to_datetime('12-05-2020', format='%d-%m-%Y')]
        
    def clean_up_testing_2 (self):
        self.fra_testing_2.loc[:, 'jour'] = pandas.to_datetime(self.fra_testing_2.loc[:, 'jour'], format='%Y-%m-%d')
        self.fra_testing_2 = self.fra_testing_2[self.fra_testing_2.loc[:,'cl_age90']==0]
        self.fra_testing_2 = self.fra_testing_2.groupby('jour').sum()
        self.fra_testing_2 = self.fra_testing_2.rename(columns={'T': 'Daily tests', 'P': 'Daily positive'})
        self.fra_testing_2 = self.fra_testing_2.loc[:, ['Daily tests', 'Daily positive']]
        self.fra_testing_2.loc[:,'Daily positive rate'] = self.fra_testing_2.loc[:,'Daily positive'].div(self.fra_testing_2.loc[:,'Daily tests'])
        
    def concat_testing (self):
        self.fra_testing = pandas.concat([self.fra_testing_1, self.fra_testing_2])
        self.fra_testing = self.fra_testing.rolling(window=7, center=True).mean()
        self.fra_testing.index = self.fra_testing.index.rename('date')
    
    def main(self):
        self.clean_up_testing_1()
        self.clean_up_testing_2()
        self.concat_testing()
        
        df_fct.export_df([['Fra_Testing', self.fra_testing]],
                          ['processed'])
        
        return self.fra_testing
    
class USTest ():
    def __init__(self):
        self.us_testing = df_fct.import_df(['US_Testing'], ['raw'])[0]
    
    def clean_up_testing (self):
        self.us_testing.loc[:,'date'] = pandas.to_datetime(self.us_testing.loc[:,'date'], format='%Y%m%d')
        self.us_testing = self.us_testing.set_index('date')
        self.us_testing = self.us_testing.loc[:,['positive', 'negative']]
        self.us_testing = self.us_testing.iloc[::-1,:]
        self.us_testing = self.us_testing.rolling(window=5, center=True).mean()
        
        self.us_testing.loc[:,'Total tests'] = self.us_testing.loc[:,'positive'] + self.us_testing.loc[:,'negative']
        self.us_testing.loc[:, 'Positive rate'] = self.us_testing.loc[:,'positive'].div(self.us_testing.loc[:,'Total tests'])
        
        self.us_testing.loc[:,'Daily positive'] = self.us_testing.loc[:,'positive'].diff()
        self.us_testing.loc[:,'Daily tests'] = self.us_testing.loc[:,'Total tests'].diff()
        self.us_testing.loc[:, 'Daily positive rate'] = self.us_testing.loc[:,'Daily positive'].div(self.us_testing.loc[:,'Daily tests'])
    
    def main(self):
        self.clean_up_testing()
        
        df_fct.export_df([['US_Testing', self.us_testing]],
                          ['processed'])
        
        return self.us_testing
        

class WorldMapDataSet():
    def __init__ (self):
        variables = ['World_JH', 'Countries_LatLong', 'World_pop']
        
        list_prop_import = ['processed', 'raw', 'raw']
        for a_var , a_prop in zip(variables, list_prop_import):
             setattr(self, a_var, df_fct.import_df([a_var],[a_prop])[0])
             
        self.world_shpe = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        
    def clean_up_CountryLatLong (self):
        self.Countries_LatLong = self.Countries_LatLong.set_index('name')
        self.Countries_LatLong.index = self.Countries_LatLong.index.rename('country')
        self.Countries_LatLong = self.Countries_LatLong.loc[:,['latitude', 'longitude']]
        
    def clean_up_WorldShp(self):
        self.world_shpe = self.world_shpe.set_index('name')
        self.world_shpe.index = self.world_shpe.index.rename('country')
        self.world_shpe = self.world_shpe.rename(index={'United States of America': 'US'})
        self.world_shpe = self.world_shpe.loc[:,['geometry']]
        
    def clean_up_pop_World (self):
        self.World_pop = self.World_pop[(self.World_pop.loc[:, 'Time']==2020) & (self.World_pop.loc[:, 'Variant']=='Medium')]
        self.World_pop = self.World_pop.drop(['LocID', 'VarID', 'Variant', 'Time', 'MidPeriod', 'PopMale', 'PopFemale', 'PopDensity'], axis=1)
        self.World_pop = self.World_pop.set_index('Location')
        self.World_pop.index = self.World_pop.index.rename('country')
        
        L1 = ['United Republic of Tanzania', 'United States of America', 'Russian Federation', 'Bolivia (Plurinational State of)', 'Venezuela (Bolivarian Republic of)', "Lao People's Democratic Republic", 'Viet Nam', 
              "Dem. People's Republic of Korea", 'Republic of Korea',"Iran (Islamic Republic of)", "Syrian Arab Republic", "Republic of Moldova", "China, Taiwan Province of China", "Brunei Darussalam", 'Western Sahara', 
              'Democratic Republic of the Congo', 'Dominican Republic', 'Falkland Islands (Malvinas)',
                                'Central African Republic', 'Equatorial Guinea', 'Eswatini', 'State of Palestine', 'Solomon Islands', 'Bosnia and Herzegovina', 'North Macedonia', 'South Sudan']
        L2 = ['Tanzania', 'US', 'Russia', 'Bolivia', 'Venezuela', 'Laos', 'Vietnam', 
              'North Korea', 'Korea, South', 'Iran', 'Syria', 'Moldova', 'Taiwan', 'Brunei', 'W. Sahara', 
              'Dem. Rep. Congo', 'Dominican Rep.', 'Falkland Is.', 'Central African Rep.', 'Eq. Guinea', 'eSwatini', 'Palestine', 'Solomon Is.', 
                                'Bosnia and Herz.', 'Macedonia', 'S. Sudan']
        
        replace_dic = dict(zip(L1,L2))
        self.World_pop = self.World_pop.rename(index=replace_dic)
        self.World_pop = self.World_pop.drop_duplicates()
        self.World_pop = self.World_pop.rename(columns={'PopTotal':'Population'})

    def append_data_world(self):
        #print(self.World_JH.index.get_level_values(0).unique())
        self.World_JH = self.World_JH.join(self.Countries_LatLong)
        self.World_JH = self.World_JH.join(self.world_shpe, how='outer')
        self.World_JH = gpd.GeoDataFrame(self.World_JH)
        
        index_WorldJH = self.World_JH.index.get_level_values(0).unique()
        for indexG in self.world_shpe.index:
            if indexG not in (index_WorldJH):
                add_index = pandas.MultiIndex.from_product([[indexG],self.World_JH.index.get_level_values(1).unique()])
                temp_df = gpd.GeoDataFrame(index=add_index, columns=self.World_JH.columns)
                try:
                    temp_df.loc[indexG, 'geometry'] = self.world_shpe.loc[indexG, 'geometry']
                    self.World_JH = self.World_JH.append(temp_df)
                    print(indexG)
                    
                except ValueError:
                    print(indexG, 'not appened')
        self.World_JH = self.World_JH.sort_index(level='country')
        
        self.World_JH = self.World_JH.join(self.World_pop)
        
        self.World_JH = self.rel_values ('World_JH')
            
    
    def main (self):
        self.clean_up_CountryLatLong ()
        self.clean_up_WorldShp()
        self.clean_up_pop_World ()
        self.append_data_world()
        df_fct.export_df([['World_pop', self.World_pop]], ['processed'])
        
        return self.World_JH
    
class USMapDataSet():

    def __init__ (self):
        variables = ['US_JH_cases', 'US_JH_death', 'US_States_shapefile', 'US_pop']
        
        list_prop_import = ['raw', 'raw', 'raw', 'raw']
        for a_var , a_prop in zip(variables, list_prop_import):
             setattr(self, a_var, df_fct.import_df([a_var],[a_prop])[0])
        
        self.df_us = pandas.DataFrame()
        
    def clean_up_USShp (self):
        self.US_States_shapefile = self.US_States_shapefile.set_index('NAME')
        self.US_States_shapefile.index = self.US_States_shapefile.index.rename('state')
        self.US_States_shapefile = self.US_States_shapefile.loc[:,'geometry']
        
    def clean_up_pop_US (self):
        self.US_pop = self.US_pop.set_index('NAME')
        self.US_pop.index = self.US_pop.index.rename('state')
        self.US_pop = self.US_pop.rename(columns={'POPESTIMATE2019':'Population'})
        
    def clean_up_data_US (self):
        list_df_us = [self.US_JH_cases, self.US_JH_death]
        list_name = ['cases', 'death']
        
        list_return = []
        for a_df, a_name in zip(list_df_us, list_name):
            a_df = a_df.groupby('Province_State').sum()
            
            if 'Population' in a_df.columns:
                a_df = a_df.drop(columns=['UID', 'code3', 'FIPS', 'Lat', 'Long_', 'Population'])
            else:
                a_df = a_df.drop(columns=['UID', 'code3', 'FIPS', 'Lat', 'Long_'])
                
            a_df.columns = pandas.to_datetime(a_df.columns)
            a_df = pandas.melt(a_df.reset_index(), id_vars=["Province_State"], value_vars=a_df.columns, var_name='date', value_name=a_name)
            a_df.loc[:,"date"] = pandas.to_datetime(a_df.loc[:,"date"])
            a_df = a_df.set_index(['Province_State', 'date'])
            a_df.index = a_df.index.rename(['state', 'date'])
            list_return.append(a_df)
            
        self.df_us = pandas.concat(list_return, axis=1).sort_index()
        self.df_us = self.add_para ('df_us', 'state')
    
    def add_para (self, df, level):
        df = getattr(self, df)
        for type_data in ['cases', 'death']:
            df.loc[:,f'delta_{type_data}'] = df.loc[:,type_data].groupby(level=level).diff()
            df.loc[:,f'growth_{type_data}'] = df.loc[:,type_data].groupby(level=level).pct_change()
            df.loc[:,f'weekly_growth_{type_data}'] = df.loc[:,type_data].groupby(level=level).pct_change(periods=7)
        df.loc[:,'fatality_rate'] = df.loc[:,'cases'].div(df.loc[:,'death'])
        
        return df
    
    def rel_values (self, df):
        df = getattr(self, df)
        for type_data in ['cases', 'death']:
            df.loc[:, f'rel_{type_data}'] = df.loc[:, type_data].div(df.loc[:, 'Population']) #cases/1000 of hab
        
        df.loc[:,'fatality_rate'] = df.loc[:,'cases'].div(df.loc[:,'death'])
        df = df.drop(columns=['Population'])
        
        return df
    
    def append_data (self, df_str, shp_df_str, pop_df_str):
        df, shp_df, pop_df, = getattr(self, df_str), getattr(self, shp_df_str), getattr(self, pop_df_str)
        df = df.join(shp_df)
        df = gpd.GeoDataFrame(df)

        df = df.join(pop_df.loc[:, 'Population'], how='inner')
        
        return df
    
    def main (self):
        self.clean_up_USShp ()
        self.clean_up_pop_US ()
        self.clean_up_data_US ()
        self.df_us = self.append_data('df_us', 'US_States_shapefile', 'US_pop')
        self.df_us = self.rel_values ('df_us')
        df_fct.export_df([['US_pop', self.US_pop]], ['processed'])
        
        return self.df_us

class FrenchMapDataSet ():
    def __init__ (self):
        variables = ['Fra_GenData', 'Fra_Regions_shapefile', 'Fra_Departements_shapefile', 'Fra_pop', 'Dept_reg']
        self.df_fra_reg = df_fct.import_df(['Fra_Reg'],['processed'])[0]
        
        list_prop_import = ['raw', 'raw', 'raw', 'raw', 'raw']
        for a_var , a_prop in zip(variables, list_prop_import):
             setattr(self, a_var, df_fct.import_df([a_var],[a_prop])[0])
        self.df_fra = pandas.DataFrame()
        self.df_fra_dpt = pandas.DataFrame()
    
    def clean_up_FraShp (self):
        self.Fra_Regions_shapefile = self.Fra_Regions_shapefile.set_index('region')
        self.Fra_Regions_shapefile = self.Fra_Regions_shapefile.loc[:,'geometry']
        
        
    def clean_up_pop_Fra (self):
        self.Fra_pop = self.Fra_pop.set_index('Région')
        self.Fra_pop.index = self.Fra_pop.index.rename('region') 
        
    def append_data (self):
        self.df_fra_reg = self.df_fra_reg.join(self.Fra_Regions_shapefile)
        self.df_fra_reg = gpd.GeoDataFrame(self.df_fra_reg)

        self.df_fra_reg = self.df_fra_reg.join(self.Fra_pop.loc[:, 'Population'], how='inner')
       
    
    def rel_values (self):
        for type_data in ['death']:
            self.df_fra_reg.loc[:, f'rel_{type_data}'] = self.df_fra_reg.loc[:, type_data].div(self.df_fra_reg.loc[:, 'Population']) #cases/1000 of hab
        
        self.df_fra_reg.loc[:,'fatality_rate'] = numpy.nan
        self.df_fra_reg = self.df_fra_reg.drop(columns=['Population'])
    
    def main (self):
        self.clean_up_pop_Fra ()
        self.clean_up_FraShp ()
        self.append_data()
        self.rel_values ()
        #df_fct.export_df([['Fra_reg_map', self.df_fra]],['processed'])
        #df_fct.export_df([['Fra_reg_pop', self.Fra_pop]], ['processed'])
        self.df_fra_reg.drop(columns=['geometry'])
        
        return self.df_fra_reg
        

if __name__ == '__main__':
    #FrenchDataSets().main()
    #df_fra_dpt_shpe= FrenchIndic().main()
    df_vax = FrenchVax ().main()
    """
    df_world = WorldDataSet().main(7, False)
    df_us = USMapDataSet().main()
    df_fra = FrenchMapDataSet().main()
    df_vax = FrenchVax ().main()
    fra_testing = FrenchTest().main()
    us_testing = USTest().main()
    """

    
    
    
    
    