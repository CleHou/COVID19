#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  1 01:20:05 2021

@author: Clement
"""
from ftplib import FTP
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import df_fct
from gen_fct import file_fct

path_dot_env = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
env_path = Path(os.path.normcase(path_dot_env+'/.env'))
load_dotenv(dotenv_path=env_path)

class FTPClass:
    def __init__ (self):
        pass
    
    def connect_ftp ():
        password= os.getenv("password")
        ftp = FTP(os.getenv("ftp"))
        user = os.getenv("user")
        
        ftp.login(user=user, passwd = password)
        etat = ftp.getwelcome()
        print(etat)
    
        return ftp
    
    def creation_folder_ftp (ftp, path):
        list_dir = path.split('/')
        list_dir = list_dir[1:]
        current_dir = '/'
        
        for a_dir in list_dir:
            ftp.cwd(current_dir) 
            list_dir = [name for name,prop in ftp.mlsd()]

            if a_dir not in list_dir:
                ftp.mkd(f'{current_dir}{a_dir}/')
                print(f'FTP directory created: {current_dir}{a_dir}/')
             
            current_dir += f'{a_dir}/'

    def disconnect (ftp):
        quitting = ftp.quit()
        print('\n' + quitting)
        
class Transfer:
    def __init__ (self, ftp, list_file, type_transfer):
        self.ftp = ftp
        self.list_file = list_file
        self.type_transfer = type_transfer
        self.db_files, self.db_file_date = df_fct.read_db_files()
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        
    def binary_transfer(self, source_path, name, k, len_tot):
        file = open(os.path.normpath(f'{source_path}/{name}'), 'rb')
        transfer = self.ftp.storbinary('STOR '+name, file)
        
        if transfer [:3] != "226":
            print('\a')
            print(transfer)
            print('\nError while transfering:', file)
            
        file.close()
            
    def renaming (self, name, extension, perma_name):
        renaming = self.ftp.rename(name, self.target_path + '/' + perma_name + extension)
            
        if renaming[:3] != "250":
            print('\a')
            print(renaming)
        
    
    def transfer (self):
        print('\n')
        print(self.db_file_date.loc[self.list_file])
        print(f'\n**** Upload type: {self.type_transfer} ****')
        print(len(self.list_file), '\nfiles groups to transfer')
        k=1
        tot_file = 0
        
        for a_file in self.list_file:
            if self.type_transfer == 'daily':
                self.target_path = self.db_files.loc[a_file, 'ftp_path']
                
            elif self.type_transfer == 'article':
                today = date.today().strftime("%Y-%m-%d")
                self.target_path = self.db_files.loc[a_file, 'ftp_path'] + f'/{today}'
            
            if self.db_files.loc[a_file, 'add_date']:
                year = self.db_file_date.loc[a_file, 'date'].strftime("%Y")
                month = self.db_file_date.loc[a_file, 'date'].strftime("%m - %B")
                day = self.db_file_date.loc[a_file, 'date'].strftime("%Y-%m-%d")
                
                self.source_path = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path']}/{year}/{month}")
                self.source_path_prev = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path_prev']}/{year}/{month}")
                name_file = self.db_files.loc[a_file, 'pref'] + day +  self.db_files.loc[a_file, 'suf']
                
            else:
                self.source_path = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path']}")
                self.source_path_prev = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path_prev']}")
                name_file = self.db_files.loc[a_file, 'pref'] + self.db_files.loc[a_file, 'suf']
                
            if self.db_files.loc[a_file, 'type_file'] == 'Graph':
                main_file = name_file + '.pdf'
                ext1 = '.pdf'
                preview_file = name_file + '_preview.png'
                ext2 = '_preview.png'
            
            elif self.db_files.loc[a_file, 'type_file'] == 'Map':
                main_file = name_file + '.html'
                ext1 = '.html'
                
            elif self.db_files.loc[a_file, 'type_file'] == 'MapPrev':
                main_file = name_file + '.png'
                ext1 = '.png'
            
            
            FTPClass.creation_folder_ftp(self.ftp, self.target_path)
            self.ftp.cwd(self.target_path)
            
            print(f'Transfering {str(k).zfill(2)}/{len(self.list_file)}: {a_file}')
            
            self.binary_transfer(self.source_path, main_file, k, len(self.list_file))
            tot_file +=1
            
            if self.type_transfer == 'daily':
                self.renaming (main_file, ext1, a_file)
            
            if self.db_files.loc[a_file, 'preview']:
                self.binary_transfer(self.source_path_prev, preview_file, k, len(self.list_file))
                tot_file +=1
                
                if self.type_transfer == 'daily':
                    self.renaming (preview_file, ext2, a_file)
            
            k+=1
            
        print('\n')
        print(f'* {tot_file} files transfered *')

class LinkExport:
    def __init__ (self, list_files, type_transfer):
        self.list_files = list_files
        self.type_transfer = type_transfer
        self.db_files, self.db_file_date = df_fct.read_db_files()
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.list_names = []

    def get_extension (self, a_file):
        if self.db_files.loc[a_file, 'type_file'] == 'Graph':
            ext = ['.pdf', '.png']
        
        elif self.db_files.loc[a_file, 'type_file'] == 'Map':
            ext = ['.html', '']
            
        elif self.db_files.loc[a_file, 'type_file'] == 'MapPrev':
            ext = ['.png', '']

        return ext

    def get_name (self, a_file):
        preview_file = ''

        if self.type_transfer == 'daily':
            main_file = a_file
            if self.db_files.loc[a_file, 'preview']:
                preview_file = a_file + '_preview'

        elif self.type_transfer == 'article':
            if self.db_files.loc[a_file, 'add_date']:
                day = self.db_file_date.loc[a_file, 'date'].strftime("%Y-%m-%d")

                main_file = self.db_files.loc[a_file, 'pref'] + day +  self.db_files.loc[a_file, 'suf']

                if self.db_files.loc[a_file, 'preview']:
                    preview_file = self.db_files.loc[a_file, 'pref'] + day +  self.db_files.loc[a_file, 'suf'] + '_preview'

            else:
                main_file = self.db_files.loc[a_file, 'pref'] + self.db_files.loc[a_file, 'suf']

                if self.db_files.loc[a_file, 'preview']:
                    preview_file = self.db_files.loc[a_file, 'pref'] + self.db_files.loc[a_file, 'suf'] + '_preview'

        return [main_file, preview_file]

            

    def return_path (self):
         for a_file in self.list_files:
            names = self.get_name(a_file)
            extensions = self.get_extension(a_file)

            if self.type_transfer == 'daily':
                self.target_path = self.db_files.loc[a_file, 'ftp_path']
                list_sub = self.target_path.split('/')
                self.target_path = 'https://houzardc.fr'
                for subfolder in list_sub[2:]:
                    self.target_path += '/' + subfolder 
                    
                
            elif self.type_transfer == 'article':
                today = date.today().strftime("%Y-%m-%d")
                self.target_path = self.db_files.loc[a_file, 'ftp_path'] + f'/{today}'
                list_sub = self.target_path.split('/')
                self.target_path = 'houzardc.fr'
                for subfolder in list_sub[2:]:
                    self.target_path += subfolder + '/'
    

            full_path = self.target_path + '/' + names[0] + extensions[0]
            self.list_names.append(full_path)

            prev_path = self.target_path + '/' + names[1] + extensions[1]
            self.list_names.append(prev_path)

    def __str__ (self):
        self.return_path()
        full_name = ''
        for a_name in self.list_names:
            if a_name[-1] != '/':
                full_name += a_name + '\n'
        return full_name
    
    def path_to_file (self):
        self.return_path()
        
        if self.type_transfer == 'daily':
            export_file = open('export_file.txt', 'w')
            
        elif self.type_transfer == 'article':
            today = date.today().strftime("%Y-%m-%d")
            export_file = open(f'export_file_{today}.txt', 'w')
            
        for a_name in self.list_names:
            if a_name[-1] != '/':
                export_file.write(a_name+'\n')
            
        export_file.close()
        print('File saved')

        

def upload (list_files, transfer_type):
    ftp = FTPClass.connect_ftp()

    Transfer(ftp, list_files, transfer_type).transfer()

    FTPClass.disconnect(ftp)
    
if __name__ == '__main__':
    list_files = ["4_countries_delta", "4_countries_growth", "world_delta", "world_growth", "stack_plot", "France_delta", "France_growth",
              "France_Gen_Situation", "France_Indic_Nat", "Map_France_Indic", "Map_France_Prev_tx_incid", "Map_France_Prev_R", "Map_France_Prev_taux_occupation_sae",
              "Map_France_Prev_tx_pos", "French_Vax", "US_Testing", "France_Testing", "All countries"]
    upload (list_files, 'daily')
    files = LinkExport(list_files, 'daily')
    files.path_to_file()


