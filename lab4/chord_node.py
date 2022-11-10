"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

Takes a port number of an existing node (or 0 to indicate it should start a new network). This program joins a new node
into the network using a system-assigned port number for itself. The node joins and then listens for incoming
connections (other nodes or queriers). You can use blocking TCP for this and pickle for the marshaling.
"""
import hashlib
import pickle
import socket
import sys
from datetime import datetime
from enum import Enum
from threading import Thread, Lock

M = hashlib.sha1().digest_size * 8
NODES = 2 ** M
BUF_SZ = 4096  # socket recv arg
BACKLOG = 100  # socket listen arg
PORT_RNG_START = 43544  # for testing use port numbers on localhost at TEST_BASE+n
PORT_RANGE_END = 65536  # end port range, allowing the members to be within avail ports
HOST = 'localhost'
TIMEOUT = 1.5
TABLE_IDX = M - 25 if M - 25 > 0 else 1
FALSE_PORT_LIST = []
NODE_ADDRESS_MAP = {}
RNG = 1


class QueryMessage(Enum):
    """
    Enum class for standardizing name calls invoked on other nodes via an RPC call.
    """
    FIND_SUCC = 'find_successor'
    FIND_PRED = 'find_predecessor'
    CPF = 'closest_preceding_finger'
    SUCC = 'successor'
    UFT = 'update_finger_table'
    SET_PRED = 'set_predecessor'
    GET_PRED = 'get_predecessor'
    ADD_KEY = 'add_key'
    GET_DATA = 'get_data'
    UPDATE_KEYS = 'update_keys'


class ModRange(object):
    """
    Range-like object that wraps around 0 at some divisor using modulo arithmetic.
    This represents the "circular-graph" that the chord network exists on.

    >> mr = ModRange(1, 4, 100)
    >> mr
    <mrange [1,4)%100>
    >> 1 in mr and 2 in mr and 4 not in mr
    True
    >> [i for i in mr]
    [1, 2, 3]
    >> mr = ModRange(97, 2, 100)
    >> 0 in mr and 99 in mr and 2 not in mr and 97 in mr
    True
    >> [i for i in mr]
    [97, 98, 99, 0, 1]
    >> [i for i in ModRange(0, 0, 5)]
    [0, 1, 2, 3, 4]
    """

    def __init__(self, start, stop, divisor):
        self.divisor = divisor
        self.start = start % self.divisor
        self.stop = stop % self.divisor
        # we want to use ranges to make things speedy, but if it wraps around the 0 node, we have to use two
        if self.start < self.stop:
            self.intervals = (range(self.start, self.stop),)
        elif self.stop == 0:
            self.intervals = (range(self.start, self.divisor),)
        else:
            self.intervals = (range(self.start, self.divisor), range(0, self.stop))

    def __repr__(self) -> str:
        """
        Something like the interval|node charts in the paper
        :return: formatted string of start and end points of interval
        """
        return ''.format(self.start, self.stop, self.divisor)

    def __contains__(self, value_id) -> bool:
        """
        Checks if the given id is within this finger's interval
        :param value_id: query key value id
        :return: True if id exist, else False
        """
        for interval in self.intervals:
            if value_id in interval:
                return True

        return False

    def __len__(self) -> int:
        """
        Override for len method, so we return the total length of all intervals
        :return:
        """
        total = 0

        for interval in self.intervals:
            total += len(interval)

        return total

    def __iter__(self) -> object:
        """
        Method to return the iterator object from ModRangeIter
        :return: the ModRangeIter object
        """
        return ModRangeIter(self, 0, -1)


class ModRangeIter(object):
    """
    Iterator class for ModRange. Allows us to iterator throughout the chord system
    to check for active Nodes
    """

    def __init__(self, mr, i, j):
        self.mr = mr
        self.i = i
        self.j = j

    def __iter__(self) -> object:
        """
        Returns the iterator object for given values
        :return: iterator object
        """
        return ModRangeIter(self.mr, self.i, self.j)

    def __next__(self) -> int:
        """
        Iterates through the interval table and returns the values at each index
        :return: int value at the index
        """
        if self.j == len(self.mr.intervals[self.i]) - 1:
            if self.i == len(self.mr.intervals) - 1:
                raise StopIteration()
            else:
                self.i += 1
                self.j = 0
        else:
            self.j += 1
        return self.mr.intervals[self.i][self.j]


class FingerEntry(object):
    """
    Row in a finger table.

    >>fe = FingerEntry(0, 1)
    >>fe

    >>fe.node = 1
    >>fe

    >> 1 in fe, 2 in fe
    (True, False)
    >> FingerEntry(0, 2, 3), FingerEntry(0, 3, 0)
    (, )
    >> FingerEntry(3, 1, 0), FingerEntry(3, 2, 0), FingerEntry(3, 3, 0)
    (, , )
    >> fe = FingerEntry(3, 3, 0)
    >> 7 in fe and 0 in fe and 2 in fe and 3 not in fe
    True
    """

    def __init__(self, n, k, node=None):
        if not (0 <= n < NODES and 0 < k <= M):
            raise ValueError('invalid finger entry values')

        self.start = (n + 2 ** (k - 1)) % NODES
        self.next_start = (n + 2 ** k) % NODES if k < M else n
        self.interval = ModRange(self.start, self.next_start, NODES)
        self.node = node

    def __repr__(self) -> str:
        """
        Something like the interval|node charts in the paper
        :return: string format of the where to start, the next start location and the node
        """
        return '{}| [{:2}, {:<2}) | '.format(self.node, self.start, self.next_start)

    def __contains__(self, value_id):
        """
        Checks if the given id is within this finger's interval
        :param value_id: query id
        :return: TODO
        """
        return value_id in self.interval


class ChordNode(object):

    def __init__(self, port, known_port=None):
        self.port = port
        self.node = self.lookup_node((HOST, port))
        self.finger = [None] + [FingerEntry(self.node, k) for k in range(1, M + 1)]  # indexing starts at 1
        self.pred = None
        self.node_keys = {}
        self.member = False  # initial state of membership for connections is set to false when initialized
        self.lock = Lock()

        # When a new member joins, a known port is passed to determine who the new connection knows in the Sys
        self.connected_node = ChordNode.lookup_node((HOST, known_port)) if known_port else None

        self.listener_server = self.initiate_listening_server()
        print('Node ID = {} is on {}'.format(self.node, (HOST, port)))
        Thread(target=self.start_server).start()

    @property
    def successor(self):
        """
        Returns the successor of the node
        :return: successor node
        """
        return self.finger[1].node

    @successor.setter
    def successor(self, value_id):
        """
        Sets the successor fo the node in the finger table to the first entry
        :param value_id: successor node
        """
        self.finger[1].node = value_id

    @property
    def predecessor(self):
        """
        returns the predecessor of the node
        :return: predecessor node
        """
        return self.pred

    @predecessor.setter
    def predecessor(self, node):
        """
        Sets the predecessor of the node
        :param node: previous node
        """
        self.pred = node

    def initiate_listening_server(self) -> socket:
        """
        Start a listening TCP server for receiving messages
        :return: listener socket
        """
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            server.bind(('localhost', self.port))
            server.listen(BACKLOG)
            return server
        except socket.error as err:
            print('Failed to bind listening_server: {}'.format(err))
            sys.exit(1)

    def start_server(self):
        """
        Starts the server and runs on a loop, listening for new conncetions with multithreading
        :return:
        """
        while True:
            if self.member:
                print('Node ID {}'.format(self.node))
            print('\nPort {}: wating for new connection...\n'.format(self.port))
            client_sock, client_add = self.listener_server.accept()
            Thread(target=self.handle_rpc, args=(client_sock,)).start()

    def handle_rpc(self, client_sock):
        """
        Handles RPC calls from other nodes sent from the thread server loop. Returns result
        of client node
        :param client_sock: the socket from the new connection
        :return:
        """
        client_rpc = client_sock.recv(BUF_SZ)
        request, val1, val2 = pickle.loads(client_rpc)

        print('Request received at {} with message: {}'.format(datetime.now().time(), request.value))
        result = self.send_rpc(request.value, val1, val2)
        client_sock.sendall(pickle.dumps(result))

    def send_rpc(self, request, val1, val2):
        """
        This method propagates the incoming query request from another node to
        the corresponding local method, based on the type of request received
        :param request: action to execute based on RPC ENUM
        :param val1: argument param
        :param val2: argument param
        :return:
        """
        # request to find successsor
        if request == QueryMessage.FIND_SUCC.value:
            return self.find_successor(val1)
        # request to return successor
        elif request == QueryMessage.SUCC.value:
            if val1:
                self.successor(val1)
            else:
                return self.successor

        # request to find closest preceding finger
        elif request == QueryMessage.CPF.value:
            return self.closest_preceding_finger(val1)

        # request to update finger table
        elif request == QueryMessage.UFT.value:
            print(self.update_finger_table(val1, val2))

        # request to set predecessor
        elif request == QueryMessage.SET_PRED.value:
            self.predecessor(val1)

        # request to get predecessor
        elif request == QueryMessage.GET_PRED.value:
            return self.predecessor

        # request to add new key
        elif request == QueryMessage.ADD_KEY.value:
            return self.add_key(val1, val2)

        # request to get data on a node
        elif request == QueryMessage.GET_DATA.value:
            return self.get_key_data(val1)

        # request to update key(s)
        elif request == QueryMessage.UPDATE_KEYS.value:
            return self.update_keys()

        else:
            print('\nQuery failed at {}: no such query exists\n'.format(datetime.now().time()))
            return None

    def call_rpc(self, node_prime, query: QueryMessage, val1=None, val2=None):
        """
        Makes an RPC call to a given method based on the query type. If no args (val1 and val2) are present
        we assume no arguments are taken.
        :param node_prime: the node to check against
        :param query: the query to make (success, predecessor, etc) dictating which method to call
        :param val1: typically the value_id to search for, if present
        :param val2: typically node data, if present
        :return: value of the called method
        """

        # if the node is already self, conduct the query
        if node_prime == self.node:
            return self.send_rpc(query, val1, val2)

        # When the node is not self, we need to figure our who to contact and send the query to
        for _ in range(RNG):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as prime_sock:
                node_prime_add = self.lookup_address(node_prime)
                prime_sock.settimeout(TIMEOUT)

                try:
                    prime_sock.connect(node_prime_add)
                    query_data = pickle.dumps((query, val1, val2))
                    prime_sock.sendall(query_data)
                    return pickle.loads(prime_sock.recv(BUF_SZ))
                except Exception as e:
                    print('Connection to node ID {} failed. Thread may be busy. Connection aborted at {}'.format(
                        node_prime, datetime.now().time()))

    def join_network(self):
        """
        New connections are added to the Chord netword, or create a new one. If a network
        exists, we require a connected_node to be known, so we can set up the new finger table
        :return:
        """
        if self.connected_node is not None:
            self.init_finger_table()
            self.update_members()
            # reorganize keys from pred since new connection is now the successor of their pred
            self.call_rpc(self.successor, QueryMessage.UPDATE_KEYS)
        else:
            for index in range(1, M + 1):
                self.finger[index].node = self.node
            self.predecessor = self.node

        self.member = True
        print('New connection established at {} with node ID [{}]'.format(datetime.now().time(), self.node))
        print('New finger table created at {}'.format((datetime.now().time())))
        self.print_node_info()

    def init_finger_table(self):
        """
        Initialize nodes finger table of successor nodes based on connected_node
        """
        self.successor = self.call_rpc(self.connected_node, QueryMessage.FIND_SUCC, self.finger[1].start)
        self.predecessor(self.call_rpc(self.successor, QueryMessage.GET_PRED))
        self.call_rpc(self.successor, QueryMessage.SET_PRED, self.node)

        for index in range(1, M):
            if self.finger[index + 1].start in ModRange(self.node, self.finger[index].node, NODES):
                self.finger[index + 1].node = self.finger[index].node
            else:
                self.finger[index + 1].node = self.call_rpc(self.connected_node, QueryMessage.FIND_SUCC, self.finger[
                    index + 1].start)

    def find_successor(self, value_id):
        """
        Ask this node to find id's successor = successor(predecessor(id))
        :param value_id: Value associated with the query key (hashed id)
        :return: successor node for the value ID
        """
        node_prime = self.find_predecessor(value_id)
        return self.call_rpc(node_prime, QueryMessage.SUCC)

    def find_predecessor(self, value_id) -> int:
        """
        Finds the predecessor of the M-bit value id and return the node
        :param value_id: Value associated with the query key (hashed id)
        :return: the predecessor node
        """
        node_prime = self.node

        while id not in ModRange(node_prime + 1, self.call_rpc(node_prime, QueryMessage.SUCC) + 1, NODES):
            node_prime = self.call_rpc(node_prime, QueryMessage.CPF, value_id)
        return node_prime

    def closest_preceding_finger(self, value_id) -> int:
        """
        Finds the node in the finger table to handle the query and returns that node to search
        for the query
        :param value_id: Value associated with the query key (hashed id)
        :return:
        """
        for index in range(M, 0, -1):
            if self.finger[index].node in ModRange(self.node + 1, value_id, NODES):
                return self.finger[index].node
            return self.node

    def update_finger_table(self, val, index):
        """
        Update the finger table is val is at index of the table
        :param val: Value to update the finger table with
        :param index: Index to check in the table
        """
        if self.finger[index].start != self.finger[index].node and val in ModRange(self.finger[index].start,
                                                                                   self.finger[index].node, NODES):
            print('Updating finger table at {}'.format(datetime.now().time()))
            self.finger[index].node = val
            pred = self.predecessor
            self.call_rpc(pred, QueryMessage.UFT, val, index)
            self.print_finger_table()
        else:
            print('No action taken on finger table for {}'.format(self.node))

    def add_key(self, key, val):
        """
        Add new key to the key:value map.
        :param key: The key in the map
        :param val: the data associated with the key
        :return:
        """
        if key >= NODES:
            raise ValueError('Error: Max ID should be {}'.format(NODES - 1))

        # if key is mine, add the value to our key list
        if key in ModRange(self.predecessor + 1, self.node + 1, NODES):
            self.node_keys[key] = val
            success = 'Key {} added at {}'.format(key, datetime.now().time())
            print(success)
            return success
        else:
            # if key is not mine, find responsible successor and add to their list
            node_prime = self.find_successor(key)
            return self.call_rpc(node_prime, QueryMessage.ADD_KEY, val)

    def get_key_data(self, key) -> int:
        """
        Returns the value associated with key
        :param key: Key to lookup
        :return: value associated with key
        """
        if key >= NODES:
            raise ValueError('Error: Max ID should be {}'.format(NODES - 1))
        # If key is mine, return the value
        if key in ModRange(self.predecessor + 1, self.node + 1, NODES):
            print('Obtained key [{}] at {}'.format(key, datetime.now().time()))
            if key in self.node_keys:
                return self.node_keys[key]
            else:
                return -1  # if key is not found in our table, -1 indicates not found
        else:
            # key is not mine, find responsible successor
            node_prime = self.find_successor(key)
            return self.call_rpc(node_prime, QueryMessage.GET_DATA, key)

    def update_members(self):
        """
        Update all connected, active members of new connection and add them to their
        finger table
        """
        # find the last node whose i-th finger might be the new node
        for index in range(1, M + 1):
            last_node = self.find_predecessor((1 + self.node - 2 ** (index - 1) + NODES) % NODES)
            self.call_rpc(last_node, QueryMessage.UFT, self.node, index)

    def update_keys(self):
        """
        Update the key list for a node. Transfer any keys to new successor from the predecessor,
        and removes the transferred keys from the list
        """
        if not self.node_keys:
            print('not action taken')
            return

        self.lock.acquire()
        removed_keys = []

        for key, value in self.node_keys.items():
            if key not in ModRange(self.predecessor + 1, self.node + 1, NODES):
                removed_keys.append(key)
                node_prime = self.find_successor(key)
                self.call_rpc(node_prime, QueryMessage.ADD_KEY, key, value)
                print('Key {} transferred to node ID [{}] at {}'.format(key, node_prime, datetime.now().time()))
        self.lock.release()

        self.remove_keys(removed_keys)
        if self.node_keys:
            print('Node keys: {}'.format(self.print_key_list()))

    def remove_keys(self, removed_keys):
        """
        Remove keys from key list
        :param removed_keys: list of keys to remove
        """
        self.lock.acquire()

        for key in removed_keys:
            del self.node_keys[key]

        self.lock.release()

    def print_node_info(self):
        """
        Helper function to print data for node
        """
        print('\n******* Member Information *******\n' \
              "Node ID: {}\n" \
              'Predecessor node: {}\n' \
              'Successor node: {}\n' \
              'Keys:\n{}\n' \
              'Finger Table:\nowner node | range |\n{}\n' \
              '**************\n'.format(self.node, self.predecessor, self.successor, self.print_key_list(),
                                        self.print_finger_table()))

    def print_key_list(self) -> str:
        """
        Helper method to print the list of keys
        :return: string message of keys
        """
        key_list = list(self.node_keys.keys())
        return ', '.join(str(key) for key in key_list) if self.node_keys else 'nothing'

    def print_finger_table(self) -> str:
        """
        Helper method to print finger table contents.
        :return: string message of finger table
        """
        return '\n'.join([str(row) for row in self.finger[TABLE_IDX:]])

    @staticmethod
    def assign_port() -> int:
        """
        Returns an available port within our port range
        :return: available port
        """
        port = 0

        while port not in range(PORT_RNG_START, PORT_RANGE_END):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_sock:
                port_sock.bind((HOST, port))
                port = port_sock.getsockname()[1]
        return port

    @staticmethod
    def lookup_address(node_prime, false_port=None) -> tuple:
        """
        Looks up the address for a given node by checking within the port range. If no address mapping is found for the
        node, we look for the address and record it.
        :param node_prime: node for address lookup
        :param false_port: possible port number that hashed to an ID that a node ID isn't
                           listening on.
        :return: (host, port) address tuple
        """
        # Create a record for ports with addresses hashed to an existing
        # node ID b/c they weren't actually listening
        if false_port:
            FALSE_PORT_LIST.append(false_port)
            del NODE_ADDRESS_MAP[node_prime]

        if node_prime not in NODE_ADDRESS_MAP:
            for port in range(PORT_RNG_START, PORT_RANGE_END):
                if port in FALSE_PORT_LIST:
                    continue  # skip bad ports

                n_prime_add = (HOST, port)
                queried_node = ChordNode.lookup_node(n_prime_add)

                if queried_node == node_prime:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        try:
                            sock.bind(n_prime_add)
                        except OSError as e:  # If binding fails, assuming node is listening at the port
                            NODE_ADDRESS_MAP[node_prime] = n_prime_add
                        except KeyError as keyerr:
                            print(keyerr)
                            return n_prime_add

        return NODE_ADDRESS_MAP[node_prime]

    @staticmethod
    def lookup_node(address) -> int:
        """
        Calls the hash function to convert the address to an M-Bit ID then returns
        that ID
        :param address: tuple (host, port)
        :return: M-Bit node ID
        """
        return ChordNode.hash_id(address) % NODES

    @staticmethod
    def query_key(node_address, key: str):
        """
        Asks a Chord node to look up a key and return the value that key is mapped to. Uses a helper method
        to talk to the node
        :param node_address: host and port of the node to submit the query to
        :param key: the key to look up
        :return: the value associated with the key in the first index (0)
        """
        return ChordNode.query_node(node_address, QueryMessage.GET_DATA, key=key)[0]

    @staticmethod
    def hash_id(data) -> int:
        """
        Hashes values using SHA1 and sorts in ascending order (Big endian)
        :param data: data to hash
        :return: shortend hashed value
        """
        hashed_data = pickle.dumps(data)
        hashed_data = hashlib.sha1(hashed_data).digest()

        # return the hashed data in ascending order
        return int.from_bytes(hashed_data, byteorder='big')

    @staticmethod
    def populate_network(address, data_keys):
        """
        Populates the chord system with the keys mapped to their data values to a given node. Uses helper method
        query_node to add data to the node
        :param address: node host and port
        :param data_keys: the dictionary of keys to add to the network
        :return: the data from the node
        """
        return ChordNode.query_node(address, QueryMessage.ADD_KEY, key_dict=data_keys)

    @staticmethod
    def query_node(node_address, query_msg: QueryMessage, key_dict=None, key=None) -> list:
        """
        Helper method for populating or querying data for a node (based on address) in the Chord network.
        :param node_address: host, port of node
        :param query_msg: Query message to call correct method
        :param key: key to pull value from (only if supplied)
        :param key_dict: dictionary of key:value pairs of data to add (only if supplied)
        :return: list of data queried or added
        """
        if query_msg != QueryMessage.ADD_KEY and query_msg != QueryMessage.GET_DATA:
            raise ValueError('Invalid query request. {} and {} requests expected.'.format(QueryMessage.ADD_KEY.value,
                                                                                          QueryMessage.GET_DATA.value))

        if key:
            key_dict = {key: None}

        query_data = []

        for key, value in key_dict.items():
            hash_id = ChordNode.hash_id(key) % NODES
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as query_sock:
                try:
                    query_sock.connect(node_address)
                    message = pickle.dumps((query_msg, hash_id, value))
                    query_sock.sendall(message)
                    query_data.append(pickle.loads(query_sock.recv(BUF_SZ)))
                except OSError as err:
                    print('RPC request [{}] failed at {}: {}'.format(query_msg, datetime.now().time(), err))
                    raise err
        return query_data


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 chord_node.py PORT (For new network, enter 0. Else, enter a connected node port)')
        exit(1)

    known_port = int(sys.argv[1])
    new_port = ChordNode.assign_port()

    if known_port == 0:
        new_node = ChordNode(new_port)
    else:
        new_node = ChordNode(new_port, known_port)

    new_node.join_network()
    new_node.start_server()