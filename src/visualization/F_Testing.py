#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 00:43:19 2021

@author: Clement
"""
import pandas
import os 
import matplotlib.pyplot as plt
import matplotlib.image as image
from matplotlib import dates
import matplotlib.lines as mlines
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
    
class Testing:
    def __init__ (self, style_cycle, intv, fig_size, country, name_df, plotting_dates, to_plot, df_title, plots_titles, data_source):
        self.style_cycle = style_cycle
        self.intv = intv
        self.country = country
        self.df = df_fct.import_df([name_df],['processed'])[0]
        self.to_plot = to_plot
        self.df_title = df_title
        self.plots_titles = plots_titles
        self.data_source = data_source
        self.fig_size = fig_size
        
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        
        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.df.index.get_level_values('date').unique()[-2])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
    
    def plot (self):
        long_date = self.plotting_dates[-1].strftime("%B %d, %Y")
        short_date = self.plotting_dates[-1].strftime("%Y-%m-%d")
        
        plotting_df = self.df.loc[self.plotting_dates[0]: self.plotting_dates[1],: ]
        fig, axs = plt.subplots(1,2, figsize=self.fig_size, num=f'Testing {self.country} {short_date}')
        k=1
        style0 = [style for style in self.style_cycle][0]
        
        for a_plot, an_axes, a_title, style in zip(self.to_plot, axs, self.plots_titles, self.style_cycle[1:]()):
            an_axes.plot(plotting_df.index, plotting_df.loc[:,a_plot[0]], label = self.df_title.loc[a_plot[0], 'Title'], **style0)
            an_axes.set_title(a_title)
            #an_axes.set_ylabel(df_title.loc[a_plot[0], 'Title'])
            an_axes.set_xlabel('Date')
            an_axes.grid()
            an_axes.tick_params(axis='y', labelcolor=style0['color'])
            an_axes.axhline(y=0.05, linestyle='--', color='#2F4F4F', linewidth=0.75)
            an_axes.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
            
            axs2 = an_axes.twinx()
            axs2.plot(plotting_df.index, plotting_df.loc[:,a_plot[1]], label = self.df_title.loc[a_plot[1], 'Title'], **style)
            #axs2.axhline(y=0.05, linestyle='--', color='#778899', linewidth=0.75)
            #axs2.set_ylabel(f"{df_title.loc[a_plot[1], 'Title']}", color=colors[k])
            axs2.tick_params(axis='y', labelcolor=style['color'])
            axs2.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
            k+=1
            
            an_axes.xaxis.set_major_formatter(dates.DateFormatter('%Y-%m-%d'))
            an_axes.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
            
        fig.autofmt_xdate()
        handles, labels = self.legend ()
        fig.legend(handles, labels, loc="center right", borderaxespad=0.5)
        plt.subplots_adjust(right=0.86)
        fig.suptitle(f"{self.country} testing report on\n{long_date}", size=16)
        
        fig.text(0.83, 0.05, f'Data source: {self.data_source} \nAnalysis: C.Houzard', fontsize=8)
        
        file_fct.save_fig (fig, f'{self.country}_Testing', self.plotting_dates[1])
            
    def legend (self):
        style0 = [style for style in self.style_cycle][0]
        
        handles, labels = [mlines.Line2D([], [], **style0)], [self.df_title.loc[self.to_plot[0][0], 'Title cut']]
        for a_plot, style in zip(self.to_plot, self.style_cycle[1:]):
            handles.append(mlines.Line2D([], [], **style))
            labels.append(self.df_title.loc[a_plot[1], 'Title cut'])
            
        return handles, labels  
    
    def main(self):
        self.plot()
    
def plot_testing_us(type_color, intv, fig_size):
    style_cycle = Cycler(type_color).main()
    
    plotting_dates = ['16-03-2020', 'last']
    to_plot = [['Daily positive rate', 'Daily positive'], ['Daily positive rate', 'Daily tests']]
    df_title = pandas.DataFrame(index=['positive', 'negative', 'Total tests', 'Positive rate',
                                'Daily positive', 'Daily tests', 'Daily positive rate'],
                                columns = ['Title', 'Title cut'],
                                data = [['Total number of cases', 'Total number of\ncases'], ['Total number of negative tests', 'Total number of\nnegative tests'], 
                                        ['Total number of tests', 'Total number of\ntests'], ['Rate of positive test (daily)', 'Rate of positive\ntest (daily)'],
                                        ['Daily number of cases', 'Daily number of\ncases'], ['Daily number of tests', 'Daily number of\ntests'], ['Rate of positive test (daily)', 'Rate of positive\ntest (daily)']])
    
    plots_titles = ['Rate of positive tests and daily number of cases', 'Rate of positive tests and daily number of tests']
    data_source = 'The COVID Tracking Project'

    Testing(style_cycle, 21, fig_size, 'US', 'US_Testing', plotting_dates, to_plot, df_title, plots_titles, data_source).main()

def plot_testing_fra(type_color, intv, fig_size):
    style_cycle = Cycler(type_color).main()
    
    plotting_dates = ['16-03-2020', 'last']
    to_plot = [['Daily positive rate', 'Daily positive'], ['Daily positive rate', 'Daily tests']]
    df_title = pandas.DataFrame(index=['Daily positive', 'Daily tests', 'Daily positive rate'],
                                columns = ['Title', 'Title cut'],
                                data = [['Daily number of cases', 'Daily number of\ncases'], ['Daily number of tests', 'Daily number of\ntests'], 
                                        ['Rate of positive test (daily)', 'Rate of positive\ntest (daily)']])
    
    plots_titles = ['Rate of positive tests and daily number of cases', 'Rate of positive tests and daily number of tests']
    data_source = 'Santé Publique France'

    Testing(style_cycle, 21, fig_size, 'France', 'Fra_Testing', plotting_dates, to_plot, df_title, plots_titles, data_source).main()
    

if __name__ == '__main__':
    fig_size = (14,7)
    plot_testing_us('color', 21, fig_size)
    plot_testing_fra('color', 21, fig_size)
        