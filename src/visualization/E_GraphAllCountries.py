#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 01:11:12 2021

@author: Clement
"""
import pandas
from matplotlib import dates
import matplotlib.pyplot as plt
import numpy
import os
import matplotlib.lines as mlines
import matplotlib.backends.backend_pdf
import matplotlib.image as image
import tqdm
import datetime
import sys
from cycler import cycler

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import df_fct
from gen_fct import file_fct

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
            style_cycle = self.line * self.linewidth * self.marker[-1:] * self.color
        else:
            style_cycle = self.color[-1:] * self.markevery_c * self.linewidth
        
        return style_cycle
    
class GraphAll:
    def __init__ (self, intv, style_cycle, df, cut_off, idx_names, sort_by, drop, per_graph, para_to_plot, plotting_dates, name_plot, title_graph):
        self.intv = intv
        self.style_cycle = style_cycle
        self.data_df = df_fct.import_df([df],['processed'])[0]
        self.cut_off = cut_off
        self.idx_names = idx_names
        self.sort_by = sort_by
        self.drop = drop
        self.per_graph = per_graph
        self.para_to_plot = para_to_plot
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        self.name_plot = name_plot
        self.title_graph = title_graph

        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.data_df.index.get_level_values('date').unique()[-1])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
    
    def select_countries (self):
        last_date = self.data_df.index.get_level_values('date').unique()[-1]
        cut_off_val = self.data_df.loc[('World', last_date), 'cases'] * self.cut_off
        considered_df = self.data_df.loc[(slice(None),last_date), ['cases']]
        considered_df = considered_df[considered_df.loc[:,['cases']]>= cut_off_val].dropna()
        self.data_df = self.data_df.loc[(considered_df.index.get_level_values('country').unique(), slice(None))]
    
    def sort_countries(self):
        grp_by_country = self.data_df.groupby(self.idx_names[0])
        # for each group, aggregate by sorting by data and taking the last row (latest date)
        latest_per_grp = grp_by_country.agg(lambda x: x.sort_values(by=self.idx_names[1]).iloc[-1])
        # sort again by cases
        sorted_by_cases = latest_per_grp.sort_values(by=self.sort_by, ascending=False)
        
        if self.drop[0]:
            sorted_by_cases = sorted_by_cases.drop(index=self.drop[1])
        
        self.list_countries = sorted_by_cases.index
    
    def chunks_list (self):
        tot_len = len(self.list_countries)
        self.list_chunks = []
      
        for j in range(tot_len//self.per_graph):
            self.list_chunks.append([self.list_countries[k+self.per_graph*j] for k in range(self.per_graph)])
    
        if self.per_graph*tot_len//self.per_graph < tot_len:     
            self.list_chunks.append([self.list_countries[k] for k in range(tot_len//self.per_graph *self.per_graph, tot_len)])
    
    def plot_everyone (self):
        long_date = self.plotting_dates[-1].strftime("%d %B, %Y")
        num_pages = len(self.list_chunks)
        list_fig = []
        
        for a_chunk, page in tqdm.tqdm(list(zip(self.list_chunks, range(num_pages+1))), desc=self.name_plot):
            sub_title = self.title(a_chunk)
            fig, axs = plt.subplots(2, 2, num=f'{self.name_plot} {page+1}/{num_pages}', figsize=(11.7, 8.3))
          
            for an_axs, a_para in zip(numpy.ravel(axs), self.para_to_plot):
                scd_axes, scd_axes_country = self.axes_or_not (a_chunk, a_para)
                    
                for a_country, style in zip(a_chunk, self.style_cycle()):
                    a_df = self.data_df.loc[(a_country, self.plotting_dates[0]): (a_country, self.plotting_dates[1]), a_para[0]]
                    a_df.index = a_df.index.remove_unused_levels()
                    list_date = a_df.index.levels[1]
    
                    if scd_axes and a_country == scd_axes_country:
                        axs2 = an_axs.twinx()
                        axs2.plot(list_date, a_df, label = a_country, **style)
                        axs2.set_ylabel(f'{a_para[0]} ({a_country})', color=style['color'])
                        axs2.tick_params(axis='y', labelcolor=style['color'])
                            
                    else:
                        an_axs.plot(list_date, a_df, **style)
                        
                an_axs.xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%y'))
                an_axs.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
                an_axs.set_xlabel('Date')
                an_axs.set_ylabel(a_para[0])
                an_axs.set_title (self.title_graph.loc[a_para[0], 'Title'])
                an_axs.grid()
                
                if a_para[1] :
                    #print( df.loc[(a_chunk[0], lim_date[-1]), a_para[0]] )
                    if isinstance(self.data_df.loc[(a_chunk[0], self.plotting_dates[-1]), a_para[0]], pandas.Series):
                       if (self.data_df.loc[(a_chunk[0], self.plotting_dates[-1]), a_para[0]]>10)[-1]:
                            an_axs.semilogy()
                            an_axs.set_ylabel(f'{a_para[0]} (log scale)')
                    elif self.data_df.loc[(a_chunk[0],  self.plotting_dates[-1]), a_para[0]]>10:
                        an_axs.semilogy()
                        an_axs.set_ylabel(f'{a_para[0]} (log scale)')
                    
            handles, labels = self.legend (a_chunk)
            
            fig.autofmt_xdate()
            fig.suptitle(f'Covid-19 situation on {long_date}\n{sub_title}', fontsize=16)
            fig.legend(handles, labels, loc="center right", borderaxespad=0.5)
            fig.subplots_adjust(right=0.85)
            fig.text(0.83, 0.05, f'Source: John Hopkins University \nGraph: C.Houzard\nPage {page+1}/{num_pages}', fontsize=8)
            
            list_fig.append(fig)
                
        file_fct.save_multi_fig (list_fig, self.name_plot, self.plotting_dates[-1])
    
    def legend (self, list_country):
        handles, labels = [], []
        for name, style in zip(list_country, self.style_cycle()):
            handles.append(mlines.Line2D([], [], **style))
            labels.append(name)
            
        return handles, labels
                    
    def axes_or_not (self, a_chunk, a_para):
        scd_axes = False
        scd_axes_country = a_chunk[0]
    
        if len(a_chunk)>1:
            val1 = self.data_df.loc[(a_chunk[0], self.plotting_dates[1]), a_para[0]]
            val2 = self.data_df.loc[(a_chunk[1], self.plotting_dates[1]), a_para[0]]
            
            if val1 > 5*val2:
                    scd_axes=True
                    
        return scd_axes, scd_axes_country
    
    def title (self, a_chunk):
        title = a_chunk[0]
        
        if len(a_chunk)>1:
            for a_country in a_chunk[1:]:
                title += f', {a_country}'
            
        return title
    
    def main(self):
        self.select_countries()
        self.sort_countries()
        self.chunks_list ()
        self.plot_everyone()
        
    
    
def plot_all_world (type_color, intv):
    style_cycle = Cycler(type_color).main()
    
    para_to_plot = [('cases', True), ('delta_cases', False), ('death', True), ('delta_death', False)]
    title_graph = pandas.DataFrame(columns=['Title'], 
                               index=['cases', 'death', 'delta_cases', 'delta_death'],
                               data = ['Number of cases', 'Number of dead', 'Daily number of cases', 'Daily number of dead'])
    plotting_dates = ['2020-03-15', 'last']
    df = GraphAll(intv, style_cycle, 'World_JH', 0.01, ['country', 'date'], 'cases', (True, 'World'), 1, para_to_plot, plotting_dates, 'All countries', title_graph).main()
    return df

def plot_all_states (type_color, intv):
    style_cycle = Cycler(type_color).main()
    
    GraphAll(intv, style_cycle).main()
    
if __name__ == '__main__':
    df = plot_all_world('color', 21)
    #plot_all_states('color', 21)
    
    
    
    
    
    
    