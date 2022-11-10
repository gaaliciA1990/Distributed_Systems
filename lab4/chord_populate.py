"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

Takes a port number of an existing node and the filename of the data file
"""
import csv
import sys
from chord_node import ChordNode

MAX = 2500  # max number of rows to pull from the csv file
HOST = 'localhost'


class PopulateChord(object):
    def __init__(self, file_name, max_rows):
        self.file_name = file_name
        self.max_rows = max_rows

    def populate_keys_from_csv(self) -> dict:
        """
        Read a csv file and create a dictionary of key:value pairs from the data in the file
        based on each row
        :param file_name: name of the csv
        :param max_rows: max number of rows to populate (optional)
        :return: key:value dictionary
        """
        file_data = {}

        with open(self.file_name) as csvfile:
            read_file = csv.reader(csvfile, delimiter=',')
            header_line = next(read_file)

            index = 0
            for row in read_file:
                index += 1
                key = row[0] + row[3]
                file_data[key] = []
                for header, cell in zip(header_line, row):
                    if cell != '--' and cell != '':
                        file_data[key].append((header, cell))
                # check if the max number of rows have been populated
                if index == self.max_rows:
                    return file_data


if __name__ == '__main__':
    """
    Executed the populate function
    """
    # expect at least 2 arguments
    if len(sys.argv) != 3:
        print("Usage: python3 chord_populate.py PORT FILENAME ")
        exit(1)

    port = int(sys.argv[1])
    file = sys.argv[2]
    address = (HOST, port)

    pop = PopulateChord(file, MAX)
    data = pop.populate_keys_from_csv()

    node = ChordNode.lookup_node(address)
    print('Requesting node {} to populate data from file {}\n'.format(node, file))

    try:
        print(ChordNode.populate_network(address, data))  # populate the data to the node and print the response
        print('\nData populated to node {}'.format(node))
    except OSError as err:
        print('\nError adding key due to: {}'.format(err))