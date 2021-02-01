#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan  9 15:56:01 2021

@author: Clement
"""
import os 
import numpy
import pandas

def list_dir_files (file_path):
    file_path = os.path.normcase(file_path)
    list_subdirr = []
    list_files = []
    for root, dirs, files in os.walk(file_path):
        list_subdirr.append(dirs)
        list_files.append(files)
        
    list_files = list(numpy.concatenate(list_files).flat)
    return list_subdirr, list_files

def get_parent_dir (n, suffix=''):
    dir_name = os.path.dirname(os.path.realpath(__file__))
    for k in range(n):
        dir_name = os.path.dirname(dir_name)
        
    dir_name = f'{dir_name}/{suffix}'       
    return dir_name

def creation_folder (root, paths):
    list_directory = [os.path.normcase(root + directory) for directory in paths]
    
    for directory in list_directory:
        if os.path.exists(directory) == False:
            print(f'Directory created: {directory}')
            os.makedirs(directory)
    list_return = [root + x for x in paths]      
    return list_return