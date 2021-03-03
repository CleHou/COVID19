#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 11:06:17 2021

@author: Clement
"""
import pandas
import os
import matplotlib.pyplot as plt
import matplotlib.image as image
import matplotlib.ticker as ticker
from matplotlib import dates
import numpy
import datetime
import holoviews as hv
import tqdm
import sys
import geopandas
import geoviews
import geoviews.tile_sources as gvts
from geoviews import dim, opts
from matplotlib import cm
from matplotlib.colors import ListedColormap
from matplotlib import colors
from bokeh.models import HoverTool
from cycler import cycler
import matplotlib.patches as mpatches

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import df_fct
from gen_fct import file_fct
from data import processing_data

class Cycler:
    def __init__ (self, type_style):
        self.color = cycler(color=['#386cb0', '#D45050', '#7fc97f', '#9A46C4', '#F08328', '#a6cee3', 'k'])
        self.color_fill = cycler(color=['#4cdc2f', '#ffb266', '#e72705'])
        self.color_fill_BW = cycler(color=['#f5f5f5', '#d6d6d6', '#808080'])
        self.alpha = cycler(alpha=[0.8, 0.2])
        self.markevery = cycler(markevery=[0.1])
        self.linewidth = cycler(linewidth=[0.75])
        self.marker = cycler(marker=['2', 4, 'o', 'x', 's', None])
        self.line = cycler(linestyle=['solid', 'dashed'])
        self.type_style=type_style

    def main(self):
        if self.type_style == 'color':
            style_cycle = self.line[:-1] * self.linewidth * self.marker[-1:] * self.color[:1]
            fill_cycle = self.color_fill * self.alpha[-1:]
        else:
            style_cycle = self.color[-1:] * self.markevery_c * self.linewidth
            fill_cycle = self.alpha[:1] * self.color_fill_BW 
        
        return style_cycle, fill_cycle

class PlotIndic:
    def __init__ (self, intv, plotting_dates, style_cycle, fill_cycle, para_to_plot, df_title):
        self.french_indic_nat = df_fct.import_df(['Fra_Indic_Nat'],['processed'])[0]
        self.intv = intv
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        self.style_cycle = style_cycle
        self.fill_cycle = fill_cycle
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.to_plot = para_to_plot
        self.df_title = df_title
        
        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.french_indic_nat.index.get_level_values('date').unique()[-1])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
            
    def plot_indicateur_nat (self):
        long_date = self.plotting_dates[-1].strftime("%d %B, %Y")
        short_date = self.plotting_dates[-1].strftime("%Y-%m-%d")
        
        new_df = self.french_indic_nat.loc[self.plotting_dates[0]:self.plotting_dates[-1]]
        
        fig, axs = plt.subplots(2,2, figsize=(15,15), num=f'Indicateurs français {short_date}')                             
        
        for axes, para, style in zip(numpy.ravel(axs), self.to_plot, self.style_cycle()):
            if numpy.isnan(new_df.loc[self.plotting_dates[0], para]):
                new_df.loc[self.plotting_dates[0], para] = 0
                
            if max(new_df.loc[:,para]) < self.df_title.loc[para, 'Val_limite'][2]:
                last_val_lim = 1.1*self.df_title.loc[para, 'Val_limite'][2]
            else : 
                last_val_lim = 1.1*max(new_df.loc[:,para])
            list_val_lim = [self.df_title.loc[para, 'Val_limite'][k] for k in range(3)]
            list_val_lim.append(last_val_lim)
                
            axes.plot(new_df.index, new_df.loc[:,para], label=self.df_title.loc[para, 'Title'], **style)
            
            for k, style in zip(range(3), self.fill_cycle()):
                axes.axhspan(list_val_lim[k], list_val_lim[k+1], **style)
        
            axes.set_title(self.df_title.loc[para, 'Title'])
            axes.set_ylabel(self.df_title.loc[para, 'Short_title'])
            axes.set_xlabel('Date')
            axes.grid()
            axes.xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%Y'))
            axes.xaxis.set_major_locator(dates.DayLocator(interval=21))
            
        fig.autofmt_xdate()
        handles, labels = self.legend(['Basse', 'Moyenne', 'Elevée'])
        fig.legend(handles, labels, loc="center right", borderaxespad=0.5, title='Criticité')
        #plt.subplots_adjust(right=0.90)
        fig.suptitle(f"French data on\n{long_date}", size=16)
        
        fig.text(0.83, 0.05, 'Data source: Santé Publique France \nAnalysis: C.Houzard', fontsize=8)
        
        file_fct.save_fig (fig, 'France_Indic_Nat', self.plotting_dates[1])

    def legend(self, title):
        handles, labels = [], []
        for label, style in zip(title, self.fill_cycle):
            handles.append(mpatches.Patch(label=label, **style))
            labels.append(label)
            
        return handles, labels
    
    def main_fct(self):
        self.plot_indicateur_nat()
    

class MapIndic:
    def __init__ (self, list_indicateur, df_title, list_color, list_cmap, parameter, off_set, step):
        self.df_indic_dpt = processing_data.FrenchIndic().main()
        self.df_indic_dpt_prev = self.df_indic_dpt
        self.list_indicateur = list_indicateur
        self.df_title = df_title
        self.list_color = list_color
        self.list_cmap = list_cmap
        self.parameter = parameter
        self.parameter_prev = parameter
        self.off_set = off_set
        self.step = step
        
        self.date_final = self.df_indic_dpt.index.get_level_values(0).max()
        self.date_ini = self.date_final- datetime.timedelta(days=self.off_set)
        slice_date = slice(self.date_ini, self.date_final, self.step)
        self.df_indic_dpt = self.df_indic_dpt.loc[(slice_date, slice(None)), :]
    
    
    def determine_color (self, an_indic, value, val_min_cmap):
        if value >= self.parameter.loc[an_indic].iloc[0] and value < self.parameter.loc[an_indic].iloc[1]:
            pctge = (value - self.parameter.loc[an_indic].iloc[0])/(self.parameter.loc[an_indic].iloc[1]-self.parameter.loc[an_indic].iloc[0])
            equi_value = int(pctge*(255-val_min_cmap) +val_min_cmap)
            color = plt.cm.Greens(equi_value)
        
        elif value >= self.parameter.loc[an_indic].iloc[1] and value < self.parameter.loc[an_indic].iloc[2]:
            pctge = (value - self.parameter.loc[an_indic].iloc[1]) /(self.parameter.loc[an_indic].iloc[2]-self.parameter.loc[an_indic].iloc[1])
            equi_value = int(pctge*(255-val_min_cmap) +val_min_cmap)
            color = plt.cm.Purples(equi_value)
            
        elif value >= self.parameter.loc[an_indic].iloc[2] and value < self.parameter.loc[an_indic].iloc[3]:
            pctge = (value - self.parameter.loc[an_indic].iloc[2])/(self.parameter.loc[an_indic].iloc[3]-self.parameter.loc[an_indic].iloc[2])
            equi_value = int(pctge*(255-val_min_cmap) +val_min_cmap)
            color = plt.cm.Reds(equi_value)
        else:
            color = (0.2, 0.2, 0.2)
                
        color = colors.to_hex(color[:3])
        return color
    
    def indicateur_dpt_plot (self):
        list_indicateur_2 = [x + '_2' for x in self.list_indicateur]
        
        for an_indic in self.parameter.index:
            val_max = 1.1*self.df_indic_dpt.loc[:,an_indic].max()
        
            if val_max < self.parameter.loc[an_indic].iloc[2]:
                val_max = 1.1*self.parameter.loc[an_indic].iloc[2]
                
            self.parameter.loc[an_indic, 'Max val'] = val_max
            
        self.df_indic_dpt = self.df_indic_dpt.reset_index()
        self.df_indic_dpt[list_indicateur_2] = self.df_indic_dpt[self.list_indicateur]
        self.df_indic_dpt = self.df_indic_dpt.rename(columns={'tx_incid': "Taux d'incidence", 'R':'Facteur de reproduction', 'taux_occupation_sae':"Taux occupation rea", 'tx_pos':'Taux positivité', 'extract_date':'Date'})
        self.df_indic_dpt = self.df_indic_dpt.drop(columns = ['region', 'tx_incid_couleur', 'R_couleur', 'taux_occupation_sae_couleur', 'tx_pos_couleur', 'nb_orange', 'nb_rouge', 'nom'])
        self.df_indic_dpt = self.df_indic_dpt.melt(id_vars=(['Date', 'departement', 'geometry', 'libelle_reg', 'libelle_dep']+list_indicateur_2), var_name='Parametre')
        
        self.parameter = self.parameter.rename(index={'tx_incid': "Taux d'incidence", 'R':'Facteur de reproduction', 'taux_occupation_sae':"Taux occupation rea", 'tx_pos':'Taux positivité'})
        
        
    def map_indicators (self):
        self.indicateur_dpt_plot ()
        
        for idx in self.df_indic_dpt.index:
            an_indic = self.df_indic_dpt.loc[idx, 'Parametre']
            color = self.determine_color (an_indic, self.df_indic_dpt.loc[idx, 'value'], 20)
            self.df_indic_dpt.at[idx, 'color'] =  color
            
        dates_to_print = [date.strftime(format='%d-%m-%Y') for date in [self.date_ini, self.date_final]]
        tooltips = [("Taux d'incidence", '@tx_incid_2'), ('Facteur de reproduction', '@R_2'), ("Taux d'occupation des lits en réa", '@taux_occupation_sae_2'),
                    ('Taux de positivité', '@tx_pos_2'), ('Région', '@libelle_reg'), ('Département', '@libelle_dep')]
        hover = HoverTool(tooltips=tooltips) 
            
        key_dimensions = ['Longitude', 'Latitude', 'Date', 'Parametre']
        MapDataSet = hv.Dataset(self.df_indic_dpt, vdims = ['value', 'color', 'libelle_reg', 'libelle_dep', 'tx_incid_2', 'R_2', 'taux_occupation_sae_2', 'tx_pos_2'], kdims = key_dimensions)
        MapDataSet = MapDataSet.to(geoviews.Polygons)
        MapRel = MapDataSet.opts(width=1000, height=560, tools=[hover],  color='color', xaxis=None, yaxis=None, title=f"Cartes des indicateurs du {dates_to_print[0]} au {dates_to_print[1]}")
        MapRel_tot= MapRel * gvts.CartoLight
        sum_map = MapRel_tot
                
        text = hv.Curve((0, 0)).opts(xaxis=None, yaxis=None) * hv.Text(0, 0, 'Source: Santé Publique France\nGraph: C.Houzard')
        MapOutput = (geoviews.Layout(sum_map + text)).cols(1)
        file_fct.save_fig (MapOutput, 'Map_France_Indic', self.date_final)
        
    def creation_cmap (self, indicateur_dpt_plot, an_indic):
        len_cmap = 100
        val_max = 1.1*indicateur_dpt_plot.loc[:,an_indic].max()
        
        if val_max < self.parameter_prev.loc[an_indic].iloc[2]:
            val_max = 1.1*self.parameter_prev.loc[an_indic].iloc[2]
        
        D1 = self.parameter_prev.loc[an_indic].iloc[1]-self.parameter_prev.loc[an_indic].iloc[0]
        D2 = self.parameter_prev.loc[an_indic].iloc[2]-self.parameter_prev.loc[an_indic].iloc[1]
        D3 = val_max-self.parameter_prev.loc[an_indic].iloc[2]
    
        list_values = []
        for cmap_name, delta in zip(self.list_cmap, [D1, D2, D3]):
            length = int(delta * len_cmap)
            cmap = cm.get_cmap(cmap_name, length)
            values = cmap(range(length))
            list_values.append(values)
        
        final_cmap = numpy.vstack(tuple(list_values))
        final_cmap = ListedColormap(final_cmap)
    
        return final_cmap, val_max
    
    def map_preview (self):
        indicateur_dpt = self.df_indic_dpt_prev.loc[[self.date_final]]
        date = self.date_final.strftime(format='%d-%m-%Y')
        
        for an_indic in tqdm.tqdm(self.list_indicateur):
            val_min = self.parameter_prev.loc[an_indic].iloc[0]
            
            final_cmap, val_max = self.creation_cmap (indicateur_dpt, an_indic)
            
            list_parameters=[hv.Dimension(an_indic, range=(val_min, val_max)), 'libelle_dep', 'libelle_reg']
            para_remove = self.list_indicateur[:]
            para_remove.remove(an_indic)
            list_parameters.extend(para_remove)
            
            MapDataSet = hv.Dataset(indicateur_dpt, vdims=list_parameters, kdims = ['Longitude', 'Latitude', 'extract_date'])
            MapDataSet = MapDataSet.to(geoviews.Polygons)
            
            MapRel = MapDataSet.opts(width=1000, height=560, tools=['hover'], colorbar=True, cmap=final_cmap, xaxis=None, yaxis=None, title=f"{self.df_title.loc[an_indic, 'Title']} on {date}")
            MapRel_tot= MapRel * gvts.CartoLight
            
            file_fct.save_fig (MapRel_tot, f'Map_France_Prev_{an_indic}', self.date_final)
            
    def main(self):
        self.map_indicators()
        self.map_preview()

    
def plotting_indic (type_color, intv):
    style_cycle, fill_cycle = Cycler(type_color).main()
    plotting_dates = ['2020-03-19', 'last']
    df_title = pandas.DataFrame(index=['tx_incid', 'R', 'taux_occupation_sae', 'tx_pos'],
                            columns=['Title', 'Short_title','Val_limite'],
                            data = [["Taux d'indicidence", "Activité épidémique (%)",(0, 10, 50)], ["Facteur de reproduction R0", '$R_0$',(0, 1, 1.5)], ['Taux d’occupation des lits en ICU', 'Tension hospitalière (%)',(0, 40, 60)], ['Taux de positivité des tests', 'Taux de positivité (%)',(0, 5, 10)]])
    para_to_plot = ['tx_incid', 'R', 'taux_occupation_sae', 'tx_pos']
    
    PlotIndic(intv, plotting_dates, style_cycle, fill_cycle, para_to_plot, df_title).main_fct()
    
def mapping_indic ():
    list_indicateur = ['tx_incid', 'R', 'taux_occupation_sae', 'tx_pos']
    df_title = pandas.DataFrame(index=['tx_incid', 'R', 'taux_occupation_sae', 'tx_pos'],
                            columns=['Title', 'Short_title','Val_limite'],
                            data = [["Taux d'indicidence", "Activité épidémique (%)",(0, 10, 50)], ["Facteur de reproduction R0", '$R_0$',(0, 1, 1.5)], ['Taux d’occupation des lits en ICU', 'Tension hospitalière (%)',(0, 40, 60)], ['Taux de positivité des tests', 'Taux de positivité (%)',(0, 5, 10)]])
    list_color = ['vert', 'orange', 'rouge']
    list_cmap = ['Greens', 'Purples', 'Reds']
    parameter = pandas.DataFrame(index=list_indicateur, columns=list_color, data=[[0, 10, 50], [0, 1, 1.5], [0, 40, 60], [0, 5, 10]])
    off_set = 20 #How long ago
    step = 4 #So many days
    
    Map = MapIndic(list_indicateur, df_title, list_color, list_cmap, parameter, off_set, step)
    Map.main()
    
    
if __name__ == '__main__':
    plotting_indic('color', 21)
    mapping_indic()
