"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

Takes a port number of an existing node and a key (any value from column 1+4 of the file)
"""
import sys

from lab4.chord_node import ChordNode

HOST = 'localhost'


class QueryChord(object):
    """
    Query a key on a single node in the Chord system from the CSV file
    """

    def __init__(self, key_id, node_addr):
        self.key = key_id
        self.node_address = node_addr
        self.node = ChordNode.lookup_node(node_addr)

    def query_data(self):
        print('Initiating query lookup with node {} for key {}....\n'.format(self.node, self.key))

        response = ChordNode.query_key(self.node_address, self.key)

        if response:
            player_id = response[0][1]
            if response[2][0] == 'Year':
                year = response[2][1]
            else:
                year = response[3][1]

            returned_key = player_id + year

            if returned_key == key:
                for tag, data in response:
                    print('{}: {}'.format(tag, data))
            else:
                print('Key hash collision detected: key [{}] doesn\'t match returned key [{}]'.format(self.key,
                                                                                                      returned_key))
        else:
            print('Data not found for query [{}]'.format(self.key))


if __name__ == '__main__':
    """
    Executes the query function to look up a key in the chord network
    """
    if len(sys.argv) != 3:
        print('Usage: python3 chord_query.py PORT KEY (format = ID + year: EX: billdemory/25127781973)')
        exit(1)

    address = (HOST, int(sys.argv[1]))
    key = sys.argv[2]

    query = QueryChord(key, address)
    query.query_data()