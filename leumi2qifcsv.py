#!/usr/bin/env python
# -*-coding=utf-8 -*-
# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2015

@author: stuart
'''

from bs4 import BeautifulSoup
import sys
import argparse
import os.path
import codecs
from datetime import datetime

#
# convert date of the form 15/07/15  ---> 2015/07/15
def reformat_date(date_string):
    timepoint = datetime.strptime(date_string, "%d/%m/%y")    
    day = timepoint.date()

    return day.isoformat()

def reformat_hebrew(hebrew_string):
    # remove "
    return hebrew_string.replace("\"", "")

def split_filename(filepath):
    import os
    path,filename_w_ext = os.path.split(filepath)
    #inputFilepath = 'path/to/file/foobar.txt'
    #filename_w_ext = os.path.basename(filepath)
    filename, file_extension = os.path.splitext(filename_w_ext)
    # filename = foobar
    # file_extension = .txt

    # path, filename = os.path.split(path / to / file / foobar.txt)
    # path = path/to/file
    # filename = foobar.txt

    return path,filename

def write_qif(file_name, qif_type, table):
    try:
        with open(file_name, 'w', encoding="utf-8") as f:
            f.write(qif_type + '\n')
            for row in table:
                for key in row:
                    f.write('{}{}\n'.format(key, row[key]))
                f.write('^\n')

    except IOError:
        # 'File not found' error message.
        print("File could not be opened")

def write_csv(file_name, qif_type, table):
    try:
        with open(file_name, 'w', encoding="utf-8") as f:
            #f.write(qif_type + '\n')
            for row in table:
                for key in row:
                    f.write('{},'.format(row[key]))
                f.write('\n')
                
    except IOError:
        # 'File not found' error message.
        print("File could not be opened")            

def write_output(file_name, qif_type, table):
    path, filename = split_filename(file_name)

    fname_qif = path + "\\" + filename + ".qif"
    fname_csv = path + "\\" + filename + ".csv"
    write_qif(fname_qif, qif_type, table)
    write_csv(fname_csv, qif_type, table)

def process_credit(input_filename, output_filename):
    """
    Testing writing qif for credit card
   """
    

    # redirecting stdout to a file (debug.txt) because writing unicode to Windows console
    # is not directlty supported (though it can be done it is coomplicated)
    print("Debug information is logged to: 'debug.txt'")
    stdout = sys.stdout
    sys.stdout = open('debug.txt', 'w', encoding="utf-8")
         
    # date memo number debit credit total
    lookup = {
              0 : 'paydate',
              1 : 'date',
              2 : 'payee',
              3 : 'number',
              4 : 'debit',
              5 : 'memo',
              6 : 'total',
              7 : 'account'
              }
     
    clean_table = []
                
    # find the tag with name 'table' and whose attribute 'class' has a value of 'dataTable'
    # in bs4 this works (for bs3 would need soup.find('table', {'class': 'dataTable'}) instead
    table = soup.find('table', class_='dataTable') 
#   print(table)
    #a = [tr.find('td') for tr in soup.findAll('tr')]
    for row in table.findAll('tr'):
    #tr = table.findAll('tr', {'class': 'alternatingItem printItem ExtendedActivity_ForPrint'})
        print("-------------------------------------------------------------------")
        s = [text for text in row.stripped_strings]
        print(s)
        
        row_stripped = {}
        idx = -1
        for td in row.findAll('td'):
            idx += 1
            value = td.get_text("|", strip=True)
            print(value)                     
            row_stripped[lookup[idx]] = value
        
        # the row may have an empty date (and some other fields because the last row in the table
        # contains the total amount spent on the card and is irrelevant
        #
        # the first row i nthe table may be a header row without values (td) so row_stripped will be empty
        #
        # Both of these cases could be avoided if we used better filters in the find/findAll functions 
        if len(row_stripped) > 0 and not row_stripped['date'] == '': 
            row_qif = {}
            row_qif['D'] = reformat_date(row_stripped['date'])                     # date
            row_qif['P'] = reformat_hebrew(row_stripped['payee'])                   # payee/description
            #row_qif['M'] = row_stripped['memo']                                   # memo/description (not used in credit/debit
            # invert the amount since it is a debit
            # figures like 3,000.00 are converted to 3000.00 (should be done using locale)
            row_qif['U'] = -1 * float(row_stripped['debit'].replace(',',''))              # amount (non-standard qif)
            row_qif['T'] = row_qif['U']                             # amount
            
                
            clean_table.append(row_qif)

    write_output(output_filename, "!Type:CCard", clean_table)
    
    sys.stdout = stdout
    
def process_bank(soup, output_filename):
    """
    Testing writing qif for checking
    """    
    
    # redirecting stdout to a file (debug.txt) because writing unicode to Windows console
    # is not directlty supported (though it can be done it is coomplicated)
    print("Debug information is logged to: 'debug.txt'")
    stdout = sys.stdout
    sys.stdout = open('debug.txt', 'w', encoding="utf-8")
         
    # date memo number debit credit total
    lookup = {
              0 : 'date',
              1 : 'memo',
              2 : 'number',
              3 : 'debit',
              4 : 'credit',
              5 : 'total'
              }
     
    clean_table = []
    
    # get the correct table            
    #     find the tag with name 'table' and whose attribute 'class' has a value of 'dataTable'
    #     in bs4 this works (for bs3 would need soup.find('table', {'class': 'dataTable'}) instead
    table = soup.find('table', class_='dataTable', id='ctlActivityTable')
    # 4/2/2017 - added id='ctlActivityTable' or would find "ctlTodayActivityTableUpper" instead
    print("hello")

    #a = [tr.find('td') for tr in soup.findAll('tr')]
    
    # loop over rows in the table. Each row is marked by the 'tr' tag
    # Note: using default html.parser sometimes fails t oextract the row correctly.
    for row in table.findAll('tr'):
    #tr = table.findAll('tr', {'class': 'alternatingItem printItem ExtendedActivity_ForPrint'})
        
        # debug code only
        print("-------------------------------------------------------------------")
        s = [text for text in row.stripped_strings]
        print(s)
        
        # loop over items in row. Each item marked by tag 'td'
        # extract the text value of the tag and strip any whitespace from it using "/" to join bits of text together
        # add the text into the dictionary row_stripped where its key is taken from lookup
        row_stripped = {}
        idx = -1
        for td in row.findAll('td'):
            idx += 1
            value = td.get_text("|", strip=True)
            print(value)                     
            row_stripped[lookup[idx]] = value
        
        # build the qif format
        if len(row_stripped) > 0: 
            row_qif = {}
            row_qif['D'] = reformat_date(row_stripped['date'])      # date
            row_qif['N']= row_stripped['number']                    # number
            row_qif['M'] = reformat_hebrew(row_stripped['memo'])    # memo or description
            
        # bank table has separate columns for debit and credit
        # need to invert the debit amount and then remove separate debit/credit to create a single figure
        # figures like 3,000.00 are converted to 3000.00 (should be done using locale)         
            if not row_stripped['debit'] == '':
                    row_qif['U'] = -1 * float(row_stripped['debit'].replace(',',''))     # amount (non-standard qif) 
            else:
                row_qif['U'] = float(row_stripped['credit'].replace(',',''))               # amount (non-standard qif)
                
            row_qif['T'] = row_qif['U']                             # amount
                
            clean_table.append(row_qif)
              
    write_output(output_filename, "!Type:Bank", clean_table)
       
    sys.stdout = stdout
            
if __name__ == '__main__':
    #locale._print_locale()
    #locale.setlocale(locale.LC_ALL, 'en_us' ) 
    # print("stdout encoding = {}".format(sys.stdout.encoding))
    # print("default encoding ={}".format(sys.getdefaultencoding()))  
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    group = parser.add_mutually_exclusive_group()
    #group.add_argument("-b", "--bank", action="store_true", help="specify input from bank statement")
    #group.add_argument("-c", "--credit", action="store_true", help="specify input from credit card statement")

    parser.add_argument('-i', dest='infile', action='store', help='intput file')
    parser.add_argument('-o', dest='outfile', action='store', help='output file')
    
    args = parser.parse_args()
       
    if os.path.exists(args.infile):
        with open(args.infile, 'r', encoding="utf-8") as file_handle:

            # need to use a parser different to the default html.parser as the deault sometimes 
            # fails on badly formed html. See http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
            # using lxml parser - needs to be installed eg from http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
            soup = BeautifulSoup(file_handle, 'lxml')
            
            # identify whether bank or credit card statement
            form = soup.body.div.find('form')
             
            if 'ExtendedActivity.aspx' in form['action']:
                print('Bank Statement')
                process_bank(soup, args.outfile)
            elif 'DisplayCreditCardActivity.aspx' in form['action']:
                print('Credit Card')
                process_credit(args.infile, args.outfile)
            else:
                print(form['action'])
                print(' is an unidentified statement type')
                parser.print_help()
          
    else:
        print("Input file does not exist")    
        
    
    
    

   
       

    
    
