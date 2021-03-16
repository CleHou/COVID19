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
        self.alpha = cycler(alpha=[0.8, 0.2])
        self.markevery = cycler(markevery=[0.1])
        self.linewidth = cycler(linewidth=[0.75])
        self.marker = cycler(marker=['2', 4, 'o', 'x', 's', None])
        self.line = cycler(linestyle=['solid', 'dashed'])
        self.type_style = type_style

    def main(self):
        if self.type_style == 'color':
            style_cycle = self.line * self.linewidth * self.marker[-1:] * self.color[:1]
        else:
            style_cycle = self.color[-1:] * self.markevery_c * self.linewidth
        
        return style_cycle
        
class FrenchVax:
    def __init__(self, style_cycle, intv, fig_size, plotting_dates):
        self.data_vax = df_fct.import_df(['Fra_Vax'],['processed'])[0]
        self.style_cycle = style_cycle
        self.intv = intv
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        self.fig_size = fig_size
        
        self.data_vax.sort_index(level=['nom','date'], inplace=True)
        
        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.data_vax.index.get_level_values('date').unique()[-2])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
    
    def plot_vax (self):
        long_date = self.plotting_dates[-1].strftime("%B %d, %Y")
        short_date = self.plotting_dates[-1].strftime("%Y-%m-%d")
        vax_j = int(self.data_vax.loc[self.data_vax.index[1],'vax journalier'] - self.data_vax.loc[self.data_vax.index[0],'vax journalier'])
        
        fig, axes = plt.subplots(1,1, figsize=self.fig_size, num=f'Nombre de vaccins {short_date}') 
        
        list_to_plot = ['total_vaccines', 'vax journalier']
        list_label = ['Total vaccinés', f'Moyenne vaccinés/j\n({vax_j}/j)']
        
        for para, title, style in zip(list_to_plot, list_label, self.style_cycle()):
            axes.plot(self.data_vax.index[:-1], self.data_vax.loc[self.data_vax.index[:-1],para], label=title, **style)
        prop_axs = axes.secondary_yaxis('right', functions=(self.nb_to_prop, self.prop_to_nb))
        #axes.axhline(y=0.6*60*10**6, linestyle='--', color='#2F4F4F', linewidth=0.75)
        
        axes.set_ylabel('Total vaccinées')
        prop_axs.set_ylabel('Prop. de la population vaccinées (%)')
        
        axes.set_xlabel('Date')
        axes.grid()
        axes.xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%Y'))
        axes.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
        
        fig.autofmt_xdate()
        
        fig.legend(loc="center right", borderaxespad=0.5)
        plt.subplots_adjust(right=0.80)
        fig.suptitle(f"Vaccines in France on\n{long_date}", size=16)
        
        fig.text(0.83, 0.05, 'Data source: Santé Publique France \nAnalysis: C.Houzard', fontsize=8)
        file_fct.save_fig (fig, 'French_Vax', self.plotting_dates[1])
        
    def nb_to_prop (self, nb):
        return nb/66 * 10**-4
    
    def prop_to_nb (self, prop):
        return prop * 66 * 10**8
    
    def main(self):
        self.plot_vax()
    
def plotting_vax (type_color, intv, fig_size):
    style_cycle = Cycler(type_color).main()
    plotting_dates = ['2020-03-19', 'last']
    
    FrenchVax(style_cycle, intv, fig_size, plotting_dates).main()
    
if __name__ == '__main__':
    fig_size = (14,7)
    plotting_vax('color', 7, fig_size)
