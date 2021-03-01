#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 02:32:53 2021

@author: Clement
"""
from src.data import data_import
from src.data import processing_data

from src.visualization import A_GenGraph
from src.visualization import BA_GenFra
from src.visualization import BB_FraIndic
from src.visualization import BC_FraVax
from src.visualization import C_Maps
from src.visualization import E_GraphAllCountries
from src.visualization import F_Testing

from src.data_transfer import ftp_transfer

type_coloring = 'color' #bw

data_import.main(1)

processing_data.FrenchDataSets().main()
processing_data.FrenchIndic().main()
processing_data.WorldDataSet().main(7, False)
processing_data.USMapDataSet().main()
processing_data.FrenchMapDataSet().main()
processing_data.FrenchVax ().main()
processing_data.FrenchTest().main()
processing_data.USTest().main()

A_GenGraph.main_gen_graph (type_coloring)
A_GenGraph.main_stack_graph (type_coloring)

BA_GenFra.main_fct (type_coloring)

BB_FraIndic.plotting_indic(type_coloring, 21)
BB_FraIndic.mapping_indic()

BC_FraVax.plotting_vax(type_coloring, 7)

#C_Maps.
#E_GraphAllCountries.

F_Testing.plot_testing_us(type_coloring, 21)
F_Testing.plot_testing_fra(type_coloring, 21)

list_files = ["4_countries_delta", "4_countries_growth", "world_delta", "world_growth", "stack_plot", "France_delta", "France_growth",
              "France_Gen_Situation", "France_Indic_Nat", "Map_France_Indic", "Map_France_Prev_tx_incid", "Map_France_Prev_R", "Map_France_Prev_taux_occupation_sae",
              "Map_France_Prev_tx_pos", "French_Vax", "US_Testing", "France_Testing"]

ftp_transfer.upload(list_files, 'daily')
print('Done')
