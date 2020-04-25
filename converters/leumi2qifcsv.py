#!/usr/bin/env python
# -*-coding=utf-8 -*-
# -*- coding: utf-8 -*-
'''
Created on Jan 6, 2015

@author: stuart
requires: bs4, lxml
'''


from bs4 import BeautifulSoup
import sys
import argparse
import os.path
import codecs
from datetime import datetime
import re


# adds a given number of months to given date string in the format of dd-mm-yyyy
# and returns a date string
def add_months_to_date(date_str, months_to_add):
    from dateutil.relativedelta import relativedelta
    date_obj = datetime.strptime(date_str, '%d/%m/%y')
    new_date_obj = date_obj + relativedelta(months=+months_to_add)
    return datetime.strftime(new_date_obj, '%d/%m/%y')


# breaks a string containing INTEGERS and returns a list of integers
# see https://www.tutorialspoint.com/How-to-extract-numbers-from-a-string-in-Python
def extract_integers_from_string(str_containing_digits):
    a = [int(s) for s in str_containing_digits.split() if s.isdigit()]
    return a


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
    writing qif for credit card
   """

    # redirecting stdout to a file (debug.txt) because writing unicode to Windows console
    # is not directly supported (though it can be done it is complicated)
    print("Debug information is logged to: 'debug.txt'")
    stdout = sys.stdout
    sys.stdout = open('debug.txt', 'w', encoding="utf-8")
         
    # date memo number debit credit total
    lookup = {
        0: 'date',
        1: 'payee',
        2: 'total',
        3: 'memo',
        4: 'details',
        5: 'debit',
        }

    clean_table = []
                
    # find the tag with name 'table' and whose attribute 'class' has a value of 'dataTable'
    # in bs4 this works (for bs3 would need soup.find('table', {'class': 'dataTable'}) instead
    table = soup.find('table', class_='xlTable')
#   print(table)
    #a = [tr.find('td') for tr in soup.findAll('tr')]
    for row in table.findAll('tr'):
        # skip any rows that contain 'xlTableTitle' or 'XlHeader' as class of any of the tds
        if not bool(row.find_all('td', class_=lambda c: c and ('xlTableTitle' in c) or ('xlHeader' in c))):
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
            print(row_stripped)
            if len(row_stripped) > 0 and not row_stripped['date'] == '':
                row_qif = {}

                # complex date handling
                # if dealing with monthly payments then use the paydate (date of debit)
                # otherwise just use the actual date of purchase
                if ("תשלום" in row_stripped['memo']):
                    deferred_paydate = row_stripped['paydate']
                    # regular expression match to string of form 03/11/18
                    match = re.search(r'\d{2}/\d{2}/\d{2}', deferred_paydate)
                    if match is not None:
                        row_qif['D'] = reformat_date(match.group())
                    else:
                        print('Could not deduce date from deffered payment - using simple date!')
                        row_qif['D'] = reformat_date(row_stripped['date'])
                else:
                    row_qif['D'] = reformat_date(row_stripped['date'].replace('.','/'))                     # date

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


def table_cell_contains(table, value_to_find):
    rc = False

    for row in table.findAll('tr'):
        # tr = table.findAll('tr', {'class': 'alternatingItem printItem ExtendedActivity_ForPrint'})

        # loop over items in row. Each item marked by tag 'td'
        # extract the text value of the tag and strip any whitespace from it using "/" to join bits of text together
        # add the text into the dictionary row_stripped where its key is taken from lookup

        idx = -1
        for td in row.findAll('td'):
            idx += 1
            value = td.get_text("|", strip=True)
            #print(value)
            if value == value_to_find:
                rc = True
                break

    return rc


def is_bank_or_creditcard(soup):
    # identify whether bank or credit card statement

    tables = soup.find_all('table')

    bank = False
    credit = False
    for t in tables:
        bank = table_cell_contains(t, 'ישיר לאומי - תנועות בחשבון')
        credit = table_cell_contains(t, 'עסקאות בש"ח')
        if bank or credit:
            break


    source = 'unknown'

    if bank:
        print('Bank Statement')
        source = 'bank'
    elif credit:
        print('Credit Card')
        source = 'credit'
    else:
        print('Unknown Statement Type')
        source = 'unknown'

    return source

def convert_excel_to_csv(file_excel, file_csv, sheet_name_to_convert):
    # TODO solve problem with Hebrew
    import pandas as pd

    # read a particular sheet
    #read_file = pd.read_excel(file_excel, sheet_name=sheet_name_to_convert, encoding='utf8')

    # read all sheets into one dataframe  - see https://pbpython.com/pandas-excel-tabs.html
    read_file = pd.concat(pd.read_excel(file_excel, sheet_name=None, encoding='utf8'), ignore_index=True)

    # need utf-8-sig to enforce utf8 BOM encoding otherwise excel doesn't read the file correctly.
    read_file.to_csv(file_csv, index=None, header=True, encoding='utf-8-sig')



if __name__ == '__main__':
    print("--- Help ---")
    print("Converts Leumi statements in html to csv or qif for importing to GnuCash")
    print("Note: Only checking and Diners credit card can be handled")
    print("Visa/Mastercard should be downloaded as Excel and converted to csv for Gnucash import")
    print("Conversion to csv is attempted automatically!")
    print("--- Help END ---")
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
            try:
                soup = BeautifulSoup(file_handle, 'lxml')

                # identify whether bank or credit card statement
                source = is_bank_or_creditcard(soup)

                if source == 'bank':
                    process_bank(soup, args.outfile)
                elif source == 'credit':
                    process_credit(args.infile, args.outfile)
                else:
                    print(' is an unidentified statement type')
                    parser.print_help()
            except:
                print("File could not be handled with BeautifulSoup - probably not html")
                print("Automatically attemtping conversion to csv...")
                convert_excel_to_csv(args.infile, args.outfile, "עסקאות במועד החיוב")
                print("Automatic conversion successful.")
    else:
        print("Input file does not exist")    
        
    
    
    

   
       

    
    
