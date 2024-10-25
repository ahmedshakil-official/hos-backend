from __future__ import print_function

import os
import sys
import logging
import csv
import argparse

logging.basicConfig(level=logging.INFO)

def parse_csv(file_name, custom_delimiter=','):
    """Generator Function for parsing csv file

    Params:
        file_name(str) -> Name of csv file
        custom_delimiters(str) : ',' -> delimiter for csv file

    Return:
        (list) A single row of a file one by one

    """

    with open(file_name, 'r') as fp:
        read_as_csv = csv.reader(fp, delimiter=custom_delimiter)
        for rows in read_as_csv:
            yield rows

def write_row(fp_name, data, custom_delimiter=','):
    """Function for write data into given file with custom delimiter

    Params:
        fp_name(str) -> File name for write data
        data(list) -> List object for write into file
        custom_delimiter(str): ',' -> delimiter for csv file

    Return:
        None
    """

    with open(fp_name, 'a') as fp:
        csv_write_obj = csv.writer(fp, delimiter=custom_delimiter, lineterminator='\n')
        if isinstance(data[0], list):
            csv_write_obj.writerows(data)
        else:
            csv_write_obj.writerows([data])

def main(file_list, output_file, headers, custom_delimiter=',', additional_columns=None):
    """Function for run all the operation together

    Params:
        file_list(list): -> List of file name to be merge
        output_file(str): -> Output file name
        headers(list): -> Header for output file
        custom_delimiter(str): ',' -> delimiter for csv file
        additional_columns(list): None -> Additional columns for output file

    Return:
        None
    """

    # initialize variables
    if not additional_columns:
        additional_columns = []
    standard_headers = [column.lower() for column in headers]
    write_row(output_file, standard_headers+additional_columns, custom_delimiter)

    # iterate over all the files
    for file_ in file_list:

        # set header for new file
        row_generator = parse_csv(file_, custom_delimiter)
        current_header = [column.lower() for column in next(row_generator)]

        # validation for columns
        missmatched_items = [column for column in standard_headers\
            if column not in current_header]
        if missmatched_items:
            logging.info('[SKIPED FILE][{}] Mismatched with header. ({})'.format(
                file_, ', '.join(missmatched_items)))
            continue

        # write data for current file
        for row in row_generator:
            data = ['' for _ in standard_headers]
            for index, column in enumerate(standard_headers):
                if column in current_header:
                    right_index = current_header.index(column)
                    data[index] = row[right_index]

            # add empty data for additional column
            data += ['' for _ in additional_columns]
            write_row(output_file, data)
        # remove the file finished copy
        if not missmatched_items:
            os.remove(file_)

if __name__ == "__main__":
    epilog = 'python csv_merge.py -f test1.csv test2.csv test3.csv' \
             ' -o output.csv -nc email post_code address'

    parser = argparse.ArgumentParser(description='Merge multiple csv file into one file.',
                                     epilog=epilog)

    parser.add_argument('-f', '--files', type=str, nargs='+',
                        required=True,
                        help='File names/path to be merge.')
    parser.add_argument('-o', '--output', type=str, required=True,
                        help='Output file name.')
    parser.add_argument('-d', '--delimiter', type=str,
                        default=',',
                        help='Custom delimiter for CSV file, default ","')
    parser.add_argument('-nc', '--ncolumn', type=str, nargs='+',
                        help='Additional columns for output file.')
    arguments = parser.parse_args()

    # check files
    if not arguments.files:
        logging.info('Enter at least 1 file name')
        exit(True)

    not_exists = False
    for each_file in arguments.files:
        if not os.path.isfile(each_file):
            logging.info('Invalid File name or path does not exists %s (exit: 1)' % each_file)
            not_exists = True
    if not_exists:
        exit(True)

    if not arguments.output or os.path.isfile(arguments.output):
        QUESTION = 'This "%s" file already exists, ' \
                    'Do you want to continue Yes/N: ' % arguments.output
        if sys.version_info.major == 2:
            # python 2 input
            confirm = raw_input(QUESTION)
        else:
            # python 3 input
            confirm = input(QUESTION)

        if confirm == 'Yes':
            os.remove(arguments.output)
        else:
            exit(True)

    if not arguments.ncolumn:
        arguments.ncolumn = []

    # list of columns to be copied or merge into new file
    list_of_columns = ['pi', 'form', 'Name', 'sp', 's1', 'b1',
                       'e1', 'strength', 'generic', 'company',
                       'full_name', 'code', 'su', 'pu', 'ps',
                       'pp', 'rack', 'b2', 's2', 'e2', 'b3', 's3',
                       'e3', 'b4', 's4', 'e4', 'b5', 's5', 'e5', 'b6',
                       's6', 'e6', 'b7', 's7', 'e7', 'b8', 's8', 'e8',
                       'b9', 's9', 'e9', 'b10', 's10', 'e10']

    main(arguments.files,
         arguments.output,
         list_of_columns,
         arguments.delimiter,
         arguments.ncolumn)
