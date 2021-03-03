#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 11:04:45 2021

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

class Cycler():
    def __init__ (self, type_style):
        self.color = cycler(color=['#386cb0', '#D45050', '#7fc97f', '#9A46C4', '#F08328', '#a6cee3', 'k'])
        self.marker = cycler(marker=['2', 4, 'o', 'x', 's', None])
        self.line = cycler(linestyle=['solid', 'dashed'])
        self.markevery = cycler(markevery=[0.3])
        self.linewidth = cycler(linewidth=[0.75])
        self.list_hatches = ['-', '+', 'x', '\\', '*', 'o', 'O', '.']
        self.type_style = type_style

    def main(self):
        if self.type_style == 'color':
            cycle = self.line[:1] * self.markevery * self.linewidth * cycler(marker=[None]) * self.color[:1]

        else:
            cycle = self.color[-1:] * self.markevery * self.linewidth

        return cycle
    
class PlotGenSituation():
    def __init__ (self, intv, plotting_dates, style_cycle, df_title, para_to_plot):
        self.french_df = df_fct.import_df(['Fra_Nat'],['processed'])[0]
        self.intv = intv
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        self.style_cycle = style_cycle
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.df_title = df_title
        self.para_to_plot = para_to_plot
        
        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.french_df.index.get_level_values('date').unique()[-1])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
    
    def reprocessing (self):
        self.french_df.loc[(self.french_df.delta_death<0),'delta_death'] = numpy.nan
        self.french_df = self.french_df.fillna(method='ffill')
        self.french_df = self.french_df.rolling(window = 7, center=False).mean()
    
    def plot (self):
        long_date = self.plotting_dates[-1].strftime("%d %B, %Y")
        month = self.plotting_dates[-1].strftime("%m - %B")
        short_date = self.plotting_dates[-1].strftime("%Y-%m-%d")
        
        new_df = self.french_df.loc[self.plotting_dates[0]:self.plotting_dates[-1]]
        
        fig, axs = plt.subplots(2,2, figsize=(15,15), num=f'Evolution of prediction on {short_date}')                             
        
        for axes, para, style in zip(numpy.ravel(axs), self.para_to_plot, self.style_cycle()):
            axes.plot(new_df.index, new_df.loc[:,para], label=self.df_title.loc[para, 'title'], **style)
            axes.set_title(self.df_title.loc[para, 'title'])
            axes.set_ylabel(self.df_title.loc[para, 'y_axis'])
            axes.set_xlabel('Date')
            axes.grid()
            axes.xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%Y'))
            axes.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
            
        fig.autofmt_xdate()
        handles, labels = axs[0][0].get_legend_handles_labels()
        #fig.legend(handles, labels, loc="center right", borderaxespad=0)
        #plt.subplots_adjust(right=0.90)
        fig.suptitle(f"French data on\n{long_date}", size=16)
        fig.autofmt_xdate()
        
        fig.text(0.83, 0.05, 'Data source: Santé Publique France \nAnalysis: C.Houzard', fontsize=8)
        
        file_fct.save_fig (fig, 'France_Gen_Situation', self.plotting_dates[1])
    
    def main(self):
        self.reprocessing ()
        self.plot()

         
def main_fct (type_color):
    cycle = Cycler(type_color).main()
    
    df_title = pandas.DataFrame(index=['reanimation', 'hospitalises', 'delta_cases', 'delta_death'],
                                columns=['title', 'y_axis'],
                                data=[['Nombre de personnes en réanimation', 'Réanimation'], ['Nombre de personnes hospitalisées', 'Hospitalisés'],['Nombre de cas journaliers', 'Cas jouranliers'],['Nombre de décès journaliers', 'Décès jouranliers']],
                                     )
    para_to_plot = ['reanimation', 'hospitalises', 'delta_cases', 'delta_death']
    
    plotting_dates = ['2020-03-15', 'last']
    fra = PlotGenSituation(21, plotting_dates, cycle, df_title, para_to_plot).main()
    return fra
    
if __name__ == '__main__':
    fra = main_fct ('color')
    
    
    
    
    
    
    
    
    
    
    
    