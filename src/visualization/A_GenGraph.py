#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  1 00:56:55 2021

@author: Clement
"""
import pandas
from matplotlib import dates
import matplotlib.pyplot as plt
import numpy
from sklearn import linear_model
from sklearn.metrics import r2_score
import os
import matplotlib.lines as mlines
import matplotlib.image as image
import sys
from cycler import cycler

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import df_fct
from gen_fct import file_fct

class Cycler():
    def __init__ (self, type_style, type_graph):
        self.type_style = type_style
        self.type_graph = type_graph
        self.color = cycler(color=['#386cb0', '#D45050', '#7fc97f', '#9A46C4', '#F08328', '#a6cee3', 'k'])
        self.marker = cycler(marker=['2', 4, 'o', 'x', 's', None])
        self.line = cycler(linestyle=['solid', 'dashed'])
        self.markevery = cycler(markevery=[0.3])
        self.linewidth = cycler(linewidth=[0.75])
        self.list_hatches = ['-', '+', 'x', '\\', '*', 'o', 'O', '.']

    def cycler_color (self):
        cycle = self.line[:1] * self.markevery * self.linewidth * self.marker[-1:] * self.color
        return cycle

    def cycler_color_stack (self):
        cycle = [self.color.by_key()['color'],[None for h in self.list_hatches]]
        return cycle

    def cycler_nb (self):
        cycle = self.color[-1:] * self.markevery * self.linewidth * self.line * self.marker[:-2]
        return cycle

    def cycler_nb_stack (self):
        cycle = [['#d6d6d6' for h in self.list_hatches],self.list_hatches]
        return cycle

    def main(self):
        if self.type_graph == 'general':
            if self.type_style == 'color':
                cycle = self.cycler_color()
            else:
                cycle = self.cycler_nb()

        elif self.type_graph == 'stack':
            if self.type_style == 'color':
                cycle = self.cycler_color_stack()
            else:
                cycle = self.cycler_nb_stack()        

        return cycle

class LinearRegression():
    def __init__ (self, prop_df, off_sets):
        self.world_df = df_fct.import_df(['World_JH'],['processed'])[0]
        self.prop_df = prop_df
        self.result_reg = pandas.DataFrame(index=prop_df.index, columns=['df_cases', 'df_death'])
        self.off_sets = off_sets
        self.list_y = []
        self.list_x_fit = []
        
        
    def data_to_fit (self, type_data, country, date_start, date_end):
        self.list_y = self.world_df.loc[(country, date_start): (country, date_end), type_data].values
        self.list_y = [numpy.log(val) for val in self.list_y]
        self.list_y = numpy.array(self.list_y)
        
        self.list_x_fit = [k for k in range(len(self.list_y))]
        self.list_x_fit = numpy.array(self.list_x_fit).reshape((-1, 1))        
    
    def build_model (self):
        regression =  linear_model.LinearRegression()
        regression.fit(self.list_x_fit, self.list_y)
        
        prediction = regression.predict(self.list_x_fit)
        list_pred = [numpy.exp(prediction[0]), numpy.exp(prediction[-1])]
        
        r2 = r2_score(self.list_y, prediction)
        coeff = regression.coef_[0]
        
        list_growth_coeff = [(coeff)*1 for k in range(2)]
        
        return regression, r2, coeff, list_growth_coeff, list_pred
        
    def eval_plot (self, regression, date_start, date_end):
        list_x = [-self.off_sets[0], self.list_x_fit[-1][0]+1+self.off_sets[1]]
        list_x =  numpy.array(list_x).reshape((-1, 1))
        
        list_pred = regression.predict(list_x)
        list_pred = [numpy.exp(val) for val in list_pred]
 
        date_beg = date_start - pandas.to_timedelta(str(self.off_sets[0])+ ' day')
        date_end = date_end + pandas.to_timedelta(str(self.off_sets[1])+ ' day')
        list_date = [date_beg, date_end]
        return list_date, list_pred
        
    def main(self):
        for country in self.prop_df.index:
            for type_data in ['cases', 'death']:
                df_reg = pandas.DataFrame(columns=['R2', 'Coeff', 'list_date', 'list_date_plot', 'list_pred', 'list_pred_xtra', 'growth_coeff'])
                k=0
                if self.prop_df.loc[country, f'Reg_{type_data}']:
                    for a_reg in prop_df.loc[country, f'Date_{type_data}']:
                        date_start = pandas.to_datetime(a_reg[0])
                        date_end = pandas.to_datetime(a_reg[1])
                        list_date = [date_start, date_end]
                        self.data_to_fit(type_data, country, date_start, date_end)
                        regression, r2, coeff, list_growth_coeff, list_pred = self.build_model ()
                        list_date_plot, list_pred_x = self.eval_plot(regression, date_start, date_end)
                        df_reg.loc[k] = [r2, coeff, list_date, list_date_plot, list_pred, list_pred_x, list_growth_coeff]
                        k+=1
                    self.result_reg.loc[country, [f'df_{type_data}']] = [df_reg]
                        
        return self.result_reg

    
class GeneralSituationGraph ():
    def __init__ (self, prop_df, plotting_dates, style_cycle, intv, result_reg, fig_size):
        self.world_df = df_fct.import_df(['World_JH'],['processed'])[0]
        self.world_df = self.world_df.ffill()
        self.prop_df = prop_df
        self.list_countries = self.prop_df.index
        self.intv = intv
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        self.style_cycle = style_cycle
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.result_reg = result_reg
        self.fig_size = fig_size
        
        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.world_df.index.get_level_values('date').unique()[-1])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
            
            
    def graph_C_and_D (self, type_graph, fig, axs):
        for country, style in zip(self.list_countries, self.style_cycle):
            df = self.world_df.loc[(country, self.plotting_dates[0]): (country, self.plotting_dates[1])]
            list_date = df.index.get_level_values('date').unique()
            axs.plot(list_date, df.loc[:,type_graph], **style)

            if self.prop_df.loc[country, f'Reg_{type_graph}']:
                df_reg = self.result_reg.loc[country, f'df_{type_graph}']
                for index in df_reg.index:
                    axs.plot(df_reg.loc[index, 'list_date_plot'], df_reg.loc[index, 'list_pred_xtra'], '--', linewidth = 0.5, color=style['color'])
                    axs.plot(df_reg.loc[index, 'list_date'], df_reg.loc[index, 'list_pred'], linewidth=0, color=style['color'], marker='2')
            
        axs.xaxis.set_major_formatter(dates.DateFormatter('%y-%m-%d'))
        axs.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
        fig.autofmt_xdate()
        
        axs.semilogy()
        
        axs.set_title (f'Cumulated number of {type_graph} vs date')
        axs.set_ylabel(f'Number of {type_graph} (log scale)')
        axs.set_xlabel('Date')
        axs.grid()
        
        
    def graph_frate (self, fig, axs):
        for country, style in zip(self.list_countries, self.style_cycle):
            df = self.world_df.loc[(country, self.plotting_dates[0]): (country, self.plotting_dates[1])]
            list_date = df.index.get_level_values('date').unique()
            axs.plot(list_date, df.loc[:,'fatality_rate'], **style)
        
        axs.xaxis.set_major_formatter(dates.DateFormatter('%y-%m-%d'))
        axs.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
        fig.autofmt_xdate()
            
        axs.set_title ('Fatality rate vs date')
        axs.set_ylabel('Fatality rate (%)')
        axs.set_xlabel('Date')
        axs.grid()
        
    def graph_grate (self, type_graph, fig, axs):
        for country, style in zip(self.list_countries, self.style_cycle):
            df = self.world_df.loc[(country, self.plotting_dates[0]): (country, self.plotting_dates[1])]
            list_date = df.index.get_level_values('date').unique()
            axs.plot(list_date, df.loc[:,f'growth_{type_graph}'], **style)

            if self.prop_df.loc[country, f'Reg_{type_graph}']:
                df_reg = self.result_reg.loc[country, f'df_{type_graph}']
                for index in df_reg.index:
                    axs.plot(df_reg.loc[index, 'list_date'], [df_reg.loc[index, 'growth_coeff'][0]*100 for k in range(2)], '--', linewidth = 0.5, color=style['color'])

        
        axs.xaxis.set_major_formatter(dates.DateFormatter('%y-%m-%d'))
        axs.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
        fig.autofmt_xdate()
            
        axs.set_title ('Growth rate of cumulated cases vs date')
        axs.set_ylabel('Growth rate (%)')
        axs.set_xlabel('Date')
        axs.grid()
        
    def graph_delta (self, type_graph, fig, axs):
        for country, style in zip(self.list_countries, self.style_cycle):
            df = self.world_df.loc[(country, self.plotting_dates[0]): (country, self.plotting_dates[1])]
            list_date = df.index.get_level_values('date').unique()
            
            if country != 'US':
                axs.plot(list_date, df.loc[:,f'delta_{type_graph}'], **style)

            else:
                axs2 = axs.twinx()
                axs2.plot(list_date, df.loc[:,f'delta_{type_graph}'], label = country, **style)
                axs2.set_ylabel(f'$\Delta$ {type_graph} (US)', color=style['color'])
                axs2.tick_params(axis='y', labelcolor=style['color'])
    
        
        axs.xaxis.set_major_formatter(dates.DateFormatter('%y-%m-%d'))
        axs.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
        fig.autofmt_xdate()
        axs.set_xlabel('Date')
        axs.set_ylabel(f'$\Delta$ {type_graph}')
        axs.set_title (f'New {type_graph} compared to d-1')
        axs.grid()
        
    def legend (self):
        handles, labels = [], []
        for label, style in zip(self.list_countries, self.style_cycle):
            handles.append(mlines.Line2D([], [], **style))
            labels.append(label)
            
        return handles, labels
        
    def layout_delta (self, fig, axs):
        self.graph_C_and_D ('cases', fig, axs[0][0])
        self.graph_C_and_D ('death', fig, axs[1][0])
        self.graph_delta ('cases', fig, axs[0][1])
        self.graph_delta ('death', fig, axs[1][1])

    def layout_growth (self, fig, axs):
        self.graph_C_and_D ('cases', fig, axs[0][0])
        self.graph_C_and_D ('death', fig, axs[1][0])
        self.graph_frate(fig, axs[0][1])
        self.graph_grate('cases', fig, axs[1][1])

    def plot (self, layout):
        long_date = self.plotting_dates[1].strftime("%B, %d %Y")
        short_date = self.plotting_dates[1].strftime("%d-%m-%Y")
        
        if len(self.list_countries) >1:
            fig, axs = plt.subplots(2, 2, num=f'Covid-19 plot {layout} on {long_date}', figsize=self.fig_size) #Grid 2x2
            
        else:
            fig, axs = plt.subplots(2, 2, num=f'Covid-19 plot {layout} {self.list_countries[-1]} on {short_date}', figsize=self.fig_size) #Grid 2x2
            
        fig.text(0.83, 0.05, 'Source: John Hopkins University\nGraph: C.Houzard', fontsize=8)
        
        if layout == 'delta':
            self.layout_delta (fig, axs)

        elif layout == 'growth':
            self.layout_growth (fig, axs)
        
        handles, labels = self.legend ()
        
        fig.legend(handles, labels, loc="center right", borderaxespad=0.5)
        fig.subplots_adjust(right=0.87)
        
        if len(self.list_countries) >1:
            fig.suptitle(f'Covid-19 situation on {long_date}', fontsize=16)
            file_fct.save_fig (fig, f'4_countries_{layout}', self.plotting_dates[1])

        else:
            if self.list_countries==['World']:
                fig.suptitle(f'Covid-19 situation worldwide on {long_date}', fontsize=16)
                file_fct.save_fig (fig, f'world_{layout}', self.plotting_dates[1])
                
            else:
                fig.suptitle(f'Covid-19 situation for {self.list_countries[-1]}\n{long_date}', fontsize=16)

                local_path=f'reports/general_graph/Countries/{self.list_countries[-1]}/PDF'
                local_path_prev=f'reports/general_graph/Countries/{self.list_countries[-1]}/png'
                ftp_path='/www/wp-content/uploads/Graphs'

                if layout == 'delta':
                    pref=f'{self.list_countries[-1]}_delta_'

                elif layout == 'growth':
                    pref=f'{self.list_countries[-1]}_growth_'

                file_fct.save_fig (fig, f'{self.list_countries[-1]}_{layout}', self.plotting_dates[1], local_path=local_path, local_path_prev=local_path_prev,
                          ftp_path=ftp_path, pref=pref, suf='', add_date=True, type_file='Graph')
        
        #plt.show()
        
    def main (self):
        self.plot ('delta')
        self.plot ('growth')
    
class StackGraph ():
    def __init__(self, cycle, list_countries, plotting_dates, intv, fig_size):
        self.world_df = df_fct.import_df(['World_JH'],['processed'])[0]
        self.cycle = cycle
        self.list_countries = list_countries
        self.plotting_dates = [pandas.to_datetime(plotting_dates[0])]
        self.intv = intv
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.fig_size = fig_size
        
        if plotting_dates[1] == 'last':
            self.plotting_dates.append(self.world_df.index.get_level_values('date').unique()[-1])
            
        else:
            self.plotting_dates.append(pandas.to_datetime(plotting_dates[0]))
    
    def ROW_df (self):
        self.plotting_df = self.world_df.loc[(self.list_countries, slice(self.plotting_dates[0], self.plotting_dates[1])),['cases', 'death']]
        temp_df = self.world_df.loc[(slice(None), slice(self.plotting_dates[0], self.plotting_dates[1])), ['cases', 'death']]
        temp_df = temp_df.drop(index=self.list_countries)
        temp_df = temp_df.drop(index='World')
        new_index = pandas.MultiIndex.from_product([['Other'], temp_df.index.get_level_values('date').unique()], names=['country', 'date'])
        df = pandas.DataFrame(index=new_index, columns=temp_df.columns,
                              data = temp_df.groupby(level='date').sum().values)
    
        self.plotting_df =pandas.concat([self.plotting_df, df])
        
    def unstack_order (self, type_graph):
        tail_ordered = self.plotting_df.groupby('country').tail(1).sort_values(by=['cases'])
        df_considered = self.plotting_df.loc[:,type_graph].unstack('date')
        df_considered = df_considered.reindex(tail_ordered.index.get_level_values('country'))
        df_considered = df_considered.fillna(method='ffill', axis=1)
        return df_considered
    
    def graph_stack (self, type_graph, incrementxy, fig, axs):
        df_considered = self.unstack_order (type_graph)
        
        list_date = df_considered.columns
        list_countries = df_considered.index
        
        prev_val = 0
        for country in list_countries:
            final_val = int(df_considered.loc[country,self.plotting_dates[-1]])
            new_val = final_val + prev_val
            #axs.annotate('+'+str(final_val), xy=(list_date[-1], new_val), xytext = (list_date[-32], new_val-incrementxy),
             #  arrowprops=dict(facecolor='black', arrowstyle="->"))
            prev_val += final_val
        
        axs.grid(alpha=0.4, zorder=4)    
        stacks = axs.stackplot(list_date, df_considered, labels = list_countries, colors = self.cycle[0][:len(list_countries)])
        for stack, hatch in zip(stacks, self.cycle[1]):
            stack.set_hatch(hatch)
        
        axs.xaxis.set_major_formatter(dates.DateFormatter('%d/%m/%y'))
        axs.xaxis.set_major_locator(dates.DayLocator(interval=self.intv))
        fig.autofmt_xdate()
        
        axs.set_title (f'Number of confirmed {type_graph} vs date')
        axs.set_ylabel(f'Number of {type_graph}')
        axs.set_xlabel('Date')
        
        
    def plot_stack (self):
        long_date = self.plotting_dates[-1].strftime("%d %B, %Y")
        
        fig, axs = plt.subplots(1, 2, num=f'Covid-19 plot on {long_date}\nStacked plot', figsize=self.fig_size) #Grid 2x2
        fig.text(0.83, 0.05, 'Source: John Hopkins University \nGraph: C.Houzard', fontsize=8)
        
        for type_graph, label_xy, axes in zip(['cases', 'death'], [50000, 500], numpy.ravel(axs)):
            self.graph_stack (type_graph, label_xy, fig, axes)
        
        handles, labels = axs[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="center right", borderaxespad=0.5)
        plt.subplots_adjust(right=0.86)
        
        fig.suptitle(f'Covid-19 situation on {long_date}', fontsize=16)
        
        file_fct.save_fig (fig, 'stack_plot', self.plotting_dates[1])

    def main(self):
        self.ROW_df()
        self.plot_stack ()
        
    
prop_df_global = pandas.DataFrame(index=['France', 'US', 'Italy', 'Germany'],
                             columns=['Reg_cases', 'Reg_death','Date_cases', 'Date_death', 'growth', 'delta'],
                             data=[[False, False, [[numpy.nan, numpy.nan]], [[numpy.nan, numpy.nan]], True, True] for k in range (4)])
plotting_dates = ['2020-03-15', 'last']

prop_df = pandas.DataFrame(index=['France'],
                             columns=['Reg_cases', 'Reg_death','Date_cases', 'Date_death', 'growth', 'delta'],
                             data=[[True, False, [['2020-10-15', '2020-11-09']], [[numpy.nan, numpy.nan]], True, True]])
plotting_dates = ['2020-03-15', 'last']

def main_gen_graph (type_color, intv, fig_size):
    cycle = Cycler(type_color, 'general').main()
    
    prop_df_global = pandas.DataFrame(index=['France', 'US', 'Italy', 'Germany'],
                             columns=['Reg_cases', 'Reg_death','Date_cases', 'Date_death', 'growth', 'delta'],
                             data=[[False, False, [[numpy.nan, numpy.nan]], [[numpy.nan, numpy.nan]], True, True] for k in range (4)])
    plotting_dates_global = ['2020-03-15', 'last']
    result_reg = LinearRegression(prop_df_global, [20,7]).main()
    GeneralSituationGraph(prop_df_global, plotting_dates_global, cycle, intv, result_reg, fig_size).main()
    
    prop_df_world = pandas.DataFrame(index=['World'],
                             columns=['Reg_cases', 'Reg_death','Date_cases', 'Date_death', 'growth', 'delta'],
                             data=[[False, False, [[]], [[]], False, True]])
    plotting_dates_world = ['2020-03-15', 'last']
    result_reg = LinearRegression(prop_df_world, [20,7]).main()
    GeneralSituationGraph(prop_df_world, plotting_dates_world, cycle, intv, result_reg, fig_size).main()
    
    prop_df_fra = pandas.DataFrame(index=['France'],
                             columns=['Reg_cases', 'Reg_death','Date_cases', 'Date_death', 'growth', 'delta'],
                             data=[[True, False, [['2020-10-15', '2020-11-09']], [[numpy.nan, numpy.nan]], True, True]])
    plotting_dates_fra = ['2020-06-05', 'last']
    result_reg = LinearRegression(prop_df_fra, [20,7]).main()
    GeneralSituationGraph(prop_df_fra, plotting_dates_fra, cycle, intv-7, result_reg, fig_size).main()

def main_stack_graph (type_color, intv, fig_size):
    list_countries = ['United Kingdom', 'Italy', 'Spain', 'France', 'US']
    plotting_dates_global = ['2020-03-15', 'last']
    cycle = Cycler(type_color, 'stack').main()
    StackGraph(cycle, list_countries, plotting_dates_global, intv, fig_size).main()

if __name__ == '__main__':
    fig_size = (14,7)
    main_gen_graph ('color', 28, fig_size)
    main_stack_graph ('color', 28, fig_size)
    


