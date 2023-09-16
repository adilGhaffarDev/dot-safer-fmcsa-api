#!/usr/bin/env python3

from urllib import request, parse
from bs4 import BeautifulSoup, element
import re
import sys
import argparse
import xlsxwriter
import time

url = 'https://safer.fmcsa.dot.gov/query.asp'

fields = {
    'LegalName': 'Legal Name:',
    'DBAName': 'DBA Name:',
    'PhysicalAddress': 'Physical Address:',
    'Phone': 'Phone:',
    'MailingAddress': 'Mailing Address:',
    'DOTNumber': 'USDOT Number:',
    'StateId': 'State Carrier ID Number:',
    'MCMXFF': 'MC/MX/FF Number(s):',
    'DUNS': 'DUNS Number:',
}

def get(id):
    try:
        params = {
            'searchType': 'ANY',
            'query_type': 'queryCarrierSnapshot',
            'query_param': 'USDOT',
            'query_string': id
        }
        data = parse.urlencode(params).encode()
        req = request.Request(url, data=data)
        resp = request.urlopen(req, timeout=40)
        return resp.read()
    except:
        print('timed out trying agin')
        time.sleep(30)
        get(id)

def parse_html(html_bytes):
    soup = BeautifulSoup(html_bytes, 'html.parser')
    hint = soup.find(string=re.compile('Entity'))

    if hint == None:
        return

    table = hint.find_parent('table')

    if table == None:
        return

    for key, field in fields.items():
        print(key, find_field(table, field))

def parse_html_return_data(html_bytes):
    soup = BeautifulSoup(html_bytes, 'html.parser')
    hint = soup.find(string=re.compile('Entity'))

    if hint == None:
        return None

    table = hint.find_parent('table')

    if table == None:
        return None
    return table

def find_field(table, label):
    th = table.find(string=label)
    tr = th.find_parent('tr')
    td = tr.find('td')

    # Could be briefer with list comprehension, but I find this more readable
    pieces = []
    for child in td.descendants:
        if type(child) != element.NavigableString:
            continue
        if child.string == None:
            continue
        normalized = child.string.replace('\\r\\n', '').strip()
        if normalized == '':
            continue
        pieces.append(normalized)

    return ' '.join(pieces)

def parse_local_file(file_path):
    with open(file_path, 'rb') as f:
        html_bytes = f.read()
        parse_html(html_bytes)

def query_by_id(id):
    try:
        html_bytes = get(id)
        parse_html(html_bytes)
    except:
        print('an error occurred')

def query_by_count(count):
        x=0
        workbook = xlsxwriter.Workbook('records.xlsx')
        worksheet = workbook.add_worksheet()
        init_excel(worksheet)
        start_usdot = 1002895
        while x<count:
            html_bytes = get(start_usdot)
            if html_bytes != None:
                table = parse_html_return_data(html_bytes)
                if table != None:
                    active = find_field(table, "Operating Status:")
                    print(active)
                    if "ACTIVE" in active:
                        row = x+1
                        col = 0
                        for key, field in fields.items():
                            worksheet.write(row, col, find_field(table, field))
                            col += 1
                            # print(key, find_field(table, field))
                        x += 1
                start_usdot+=1
            print(x)
        workbook.close()

def init_excel(worksheet):
    # Workbook() takes one, non-optional, argument
    # which is the filename that we want to create.
    # workbook = xlsxwriter.Workbook('records.xlsx')
 
    # The workbook object is then used to add new
    # worksheet via the add_worksheet() method.
    # worksheet = workbook.add_worksheet()
 
    # Use the worksheet object to write
    # data via the write() method.
    # 'LegalName': 'Legal Name:',
    # 'DBAName': 'DBA Name:',
    # 'PhysicalAddress': 'Physical Address:',
    # 'Phone': 'Phone:',
    # 'MailingAddress': 'Mailing Address:',
    # 'DOTNumber': 'USDOT Number:',
    # 'StateId': 'State Carrier ID Number:',
    # 'MCMXFF': 'MC/MX/FF Number(s):',
    # 'DUNS': 'DUNS Number:',
    worksheet.write('A1', 'LegalName')
    worksheet.write('B1', 'DBAName')
    worksheet.write('C1', 'PhysicalAddress')
    worksheet.write('D1', 'Phone')
    worksheet.write('E1', 'MailingAddress')
    worksheet.write('F1', 'DOTNumber')
    worksheet.write('G1', 'StateId')
    worksheet.write('H1', 'MCMXFF')
    worksheet.write('I1', 'DUNS')
    # Finally, close the Excel file
    # via the close() method.
    # workbook.close()

# def save_in_excel(table):


def save_by_id(id):
    try:
        html_bytes = get(id)
        with open('./saved/' + id + '.html', 'wb') as f:
            f.write(html_bytes)
    except:
        print('an error occurred')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse information from US DOT API')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--parse', dest='file', type=str, help='Parse data from a local file')
    group.add_argument('--query', dest='id', type=str, help='USDOT id to query live from the API and print the parsed data')
    group.add_argument('--all', dest='count', type=int, help='List all')

    args = parser.parse_args()

    if args.file:
        parse_local_file(args.file)
    elif args.id:
        query_by_id(args.id)
    elif args.count:
        query_by_count(args.count)
    else:
        parser.print_help(sys.stdout)
