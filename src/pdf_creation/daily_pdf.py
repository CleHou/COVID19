#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  17 12:33:39 2021

@author: Clement
"""
import pandas
import PyPDF2
import os
import sys
import docx
from docxtpl import DocxTemplate
from docx2pdf import convert

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from gen_fct import df_fct
from gen_fct import file_fct

class merging_pdf:
    def __init__ (self, list_files):
        self.db_files, self.db_file_date = df_fct.read_db_files()
        self.root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        self.date = pandas.to_datetime('today')
        self.list_files = list_files

    def full_path (self, a_file):
        if self.db_files.loc[a_file, 'add_date']:
            year = self.db_file_date.loc[a_file, 'date'].strftime("%Y")
            month = self.db_file_date.loc[a_file, 'date'].strftime("%m - %B")
            day = self.db_file_date.loc[a_file, 'date'].strftime("%Y-%m-%d")
	        
            source_path = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path']}/{year}/{month}")
            source_path_prev = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path_prev']}/{year}/{month}")
            name_file = self.db_files.loc[a_file, 'pref'] + day +  self.db_files.loc[a_file, 'suf']
        
        else:
            source_path = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path']}")
            source_path_prev = os.path.normpath(f"{self.root}/{self.db_files.loc[a_file, 'local_path_prev']}")
            name_file = self.db_files.loc[a_file, 'pref'] + self.db_files.loc[a_file, 'suf']

        full_name = os.path.normpath(f'{source_path}/{name_file}.pdf')

        return full_name


    def merging_pdf (self, full_path):
        pdf_writer = PyPDF2.PdfFileWriter()
        
        file = open(full_path, 'rb')
        file_reader = PyPDF2.PdfFileReader(file)
        for page_num in range(file_reader.numPages):
            page_object = file_reader.getPage(page_num)
            pdf_writer.addPage(page_object)
        #os.remove(full_path)
                
        for a_file in self.list_files:
            if self.db_files.loc[a_file, 'type_file'] == 'Graph':
                full_name = self.full_path (a_file) 
                file = open(full_name, 'rb')
                file_reader = PyPDF2.PdfFileReader(file)
	                
                for page_num in range(file_reader.numPages):
                    page_object = file_reader.getPage(page_num)
                    pdf_writer.addPage(page_object)
                    
        file_fct.save_pdf (pdf_writer, self.date)
        file.close()
        os.remove(full_path)
        
    def var_template (self):
        final_dic = {}
        final_dic['date'] = self.date.strftime("%Y-%m-%d")
        
        full_list = []
        page = 2
        for a_file in self.list_files:
            if self.db_files.loc[a_file, 'type_file'] == 'Graph':
                full_list.append({'name': a_file,
                                  'page': page})
                
                full_name = self.full_path (a_file) 
                file = open(full_name, 'rb')
                file_reader = PyPDF2.PdfFileReader(file)
                page += file_reader.numPages
            
        final_dic['list_file'] = full_list
        
        return final_dic
    
    def fill_template (self):
        context = self.var_template()
        
        path_to_template = os.path.normpath(f'{self.root}/src/pdf_creation/template.docx')
        template = DocxTemplate(path_to_template)
        
        template.render (context)
        
        date_str = self.date.strftime("%Y-%m-%d")
        year = self.date.strftime("%Y")
        month = self.date.strftime("%m - %B")
    
        file_dir = f"{self.root}/reports/Daily_PDF/{year}/{month}"
        file_name = f"First_page_{date_str}"
        file_fct.creation_folder ('', [file_dir])
        full_path = os.path.normcase(f'{file_dir}/{file_name}.docx')
        
        template.save(full_path)
        convert(full_path)
        os.remove(full_path)
        
        return os.path.normcase(f'{file_dir}/{file_name}.pdf')
        
        
    def main (self):
        full_path = self.fill_template()
        self.merging_pdf(full_path)
 

if __name__ == '__main__':
	list_files = ["4_countries_delta", "4_countries_growth", "world_delta", "world_growth", "stack_plot", "France_delta", "France_growth",
					"France_Gen_Situation", "France_Indic_Nat", "Map_France_Indic", "Map_France_Prev_tx_incid", "Map_France_Prev_R", "Map_France_Prev_taux_occupation_sae",
              "Map_France_Prev_tx_pos", "French_Vax", "US_Testing", "France_Testing", "All countries"]

	merging_pdf(list_files).main()
