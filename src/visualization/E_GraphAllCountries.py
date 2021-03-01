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
    def __init__ (self, intv, style_cycle):
        pass
    
    def select_countries (df_world, pctg):
        last_date = df_world.index[-1][1]
        cut_off_val = df_world.loc[('World', last_date), 'Cases'] * pctg
        print(cut_off_val)
        list_countries = df_world.index.levels[0]
        
        for a_country in list_countries:
            if df_world.loc[(a_country, last_date), 'Cases'] < cut_off_val:
                df_world = df_world.drop(index=a_country)
    
        return df_world
    
    def sort_countries(df, idx1, idx2, para, drop):
        grp_by_country = df.groupby(idx1)
        # for each group, aggregate by sorting by data and taking the last row (latest date)
        latest_per_grp = grp_by_country.agg(lambda x: x.sort_values(by=idx2).iloc[-1])
        # sort again by cases
        sorted_by_cases = latest_per_grp.sort_values(by=para, ascending=False)
        
        if drop[0]:
            sorted_by_cases = sorted_by_cases.drop(index=drop[1])
        
        return sorted_by_cases.index
    
     
    def num_countries (df_world):
        list_len = []
        list_pctge = numpy.logspace(-3, -1, 30)
        for a_pctge in tqdm.tqdm(list_pctge):
            df_world = select_countries (df_world, a_pctge)
            list_len.append(len(df_world.index.levels[0]))
        
        plt.figure('Test pctge')
        plt.plot(list_pctge, list_len, linewidth=0.75, marker='2')
        plt.xlabel('% of total world cases')
        plt.ylabel('Number of countries matching criteria')
        plt.grid()
        plt.show()       
    
    def legend (list_country, colors):
        list_zip = zip(list_country, colors)
        handles, labels = [], []
        for element in list_zip:
            handles.append(mlines.Line2D([], [], color=element[1], marker = '2', linewidth=0.75))
            labels.append(element[0])
            
        return handles, labels
    
        
    def chunks_list (list_countries, val):
        tot_len = len(list_countries)
        list_chunks = []
      
        for j in range(tot_len//val):
            list_chunks.append([list_countries[k+val*j] for k in range(val)])
    
        if val*tot_len//val < tot_len:     
            list_chunks.append([list_countries[k] for k in range(tot_len//val *val, tot_len)])
            
        return list_chunks
    
    def plot_everyone (df, region_to_plot, para_to_plot, lim_date, title_graph, colors, intv, titre_pdf, titre_preview, tqdm_name, logo):
        long_date = lim_date[1].strftime("%d %B, %Y")
        
        num_pages = len(region_to_plot)
        pdf = matplotlib.backends.backend_pdf.PdfPages(os.path.normcase(titre_pdf))
        
        preview=True
       
        for a_chunk, page in tqdm.tqdm(list(zip(region_to_plot, range(num_pages+1))), desc=tqdm_name):
            sub_title = title(a_chunk)
            fig, axs = plt.subplots(2, 2, num=f'{titre_pdf} {page+1}/{num_pages}', figsize=(11.7, 8.3))
          
            for an_axs, a_para in zip(numpy.ravel(axs), para_to_plot):
                scd_axes, scd_axes_country = axes_or_not (df, a_chunk, a_para)
                    
                for a_country, a_color in zip(a_chunk, colors):
                    a_df = df.loc[(a_country, lim_date[0]): (a_country, lim_date[1]), a_para[0]]
                    a_df.index = a_df.index.remove_unused_levels()
                    list_date = a_df.index.levels[1]
    
                    if scd_axes and a_country == scd_axes_country:
                        axs2 = an_axs.twinx()
                        axs2.plot(list_date, a_df, linewidth=0.75, label = a_country, color = a_color)
                        axs2.set_ylabel(f'{a_para[0]} ({a_country})', color=a_color)
                        axs2.tick_params(axis='y', labelcolor=a_color)
                            
                    else:
                        an_axs.plot(list_date, a_df, linewidth=0.75, color = a_color)
                        
                an_axs.xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%y'))
                an_axs.xaxis.set_major_locator(dates.DayLocator(interval=intv))
                an_axs.set_xlabel('Date')
                an_axs.set_ylabel(a_para[0])
                an_axs.set_title (title_graph.loc[a_para[0], 'Title'])
                an_axs.grid()
                
                if a_para[1] :
                    #print( df.loc[(a_chunk[0], lim_date[-1]), a_para[0]] )
                    if isinstance(df.loc[(a_chunk[0], lim_date[-1]), a_para[0]], pandas.Series):
                       if (df.loc[(a_chunk[0], lim_date[-1]), a_para[0]]>10)[-1]:
                            an_axs.semilogy()
                            an_axs.set_ylabel(f'{a_para[0]} (log scale)')
                    elif df.loc[(a_chunk[0], lim_date[-1]), a_para[0]]>10:
                        an_axs.semilogy()
                        an_axs.set_ylabel(f'{a_para[0]} (log scale)')
                    
            handles, labels = legend (a_chunk, colors)
            
            fig.autofmt_xdate()
            fig.suptitle(f'Covid-19 situation on {long_date}\n{sub_title}', fontsize=16)
            fig.legend(handles, labels, loc="center right")
            fig.subplots_adjust(right=0.85)
            fig.figimage(logo, 30, 20, zorder=3)
            fig.text(0.83, 0.05, f'Source: John Hopkins University \nGraph: C.Houzard\nPage {page+1}/{num_pages}', fontsize=8)
            #plt.tight_layout()
            pdf.savefig(fig, dpi=200)
            
            if preview:
                fig.savefig(os.path.normcase(titre_preview), format='png', dpi=300)
                preview=False
                #fig.savefig(os.path.normcase(titre_preview + a_chunk[0]+'.png'), format='png', dpi=300)
            plt.close(fig)
                
        pdf.close()
                    
    def axes_or_not (df_world, a_chunk, a_para):
        scd_axes = False
        scd_axes_country = a_chunk[0]
    
        if len(a_chunk)>1:
            val1 = df_world.loc[(a_chunk[0], lim_date[1]), a_para[0]]
            val2 = df_world.loc[(a_chunk[1], lim_date[1]), a_para[0]]
            
            if val1 > 5*val2:
                    scd_axes=True
                    
        return scd_axes, scd_axes_country
    
    def title (a_chunk):
        title = a_chunk[0]
        
        if len(a_chunk)>1:
            for a_country in a_chunk:
                title += f', {a_chunk}'
            
        return title
    
    def main(self):
        pass
    
    
def plot_all_world (type_color, intv):
    style_cycle = Cycler(type_color).main()
    
    GraphAll(intv, style_cycle).main()

def plot_all_states (type_color, intv):
    style_cycle = Cycler(type_color).main()
    
    GraphAll(intv, style_cycle).main()
    
if __name__ == '__main__':
    plot_all_world('color', 21)
    plot_all_states('color', 21)
    
    
    
    
    
    
    