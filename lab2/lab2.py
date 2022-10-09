"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0
"""
from datetime import date
import selectors
import socket
import pickle
import sys
from enum import Enum


class BullyClient:
    """
    The Bully Client will send and receive messages to determine who is the leader (bully)
    in the server. The process is run synchronously to handle all connections and messages
    """

    def __init__(self, host, port, next_bday, su_id):
        self.gcd_address = (host, int(port))

        days_to_bd = (next_bday - date.today()).days  # determine the number of days till their next bday
        self.process_id = (days_to_bd, su_id)

        self.member_connections = {}  # creating dictionary for holding connected members
        self.member_states = {}  # creating dictionary for holding member states
        self.leader = None  # election pending as indicated by None
        self.selector = selectors.DefaultSelector()

        self.listening_server = self.create_listening_server()

        self.BUF_SIZE = 1024
        self.timeout = float(1.500)
        self.failed_msg = 'Failed to connect: '
        self.client_state = State.QUIESCENT  # set our state to default

    def connect(self):
        """
        This method will set up the connection to the GCD server and run the other
        processes for handling outgoing and incoming messages
        :return:
        """
        # Set up connection with the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print('Contacting GCD Server...\n')
            # check we connect to the server successfully
            if self.contact_gcd_server(sock, self.gcd_address[0], self.gcd_address[1]) is False:
                sys.exit(1)

            print('Successfully connected to GCD Server...\n')
            join_msg = ('JOIN', (self.process_id, self.gcd_address))
            sock.sendall(pickle.dumps(join_msg))
            self.member_connections = pickle.loads(sock.recv(self.BUF_SIZE))
            print(self.member_connections)

            while True:
                events = self.selector.select()
                for key, mask in events:
                    callback = key.data  # reference variable to the data passed in selector.register
                    callback(key.fileobj, mask)

    def contact_gcd_server(self, connection, host, port):
        """
        This function will handle the connection checks. If connection failed, return false
        else true
        :param connection: the socket stream
        :param host: host address to connect to
        :param port: port to connect to
        :return: false if connection failse, otherwise true
        """
        # First try the connect, if failed, we display the message and exit
        try:
            connection.settimeout(self.timeout)
            connection.connect((host, port))
            return True
        except socket.timeout as to:
            print(self.failed_msg, repr(to))
            return False
        except OSError as err:
            print(self.failed_msg, repr(err))
            return False

    def create_listening_server(self):
        """
        Creating a listening server so peers can connect to my client
        :return: tuple of the listener connection and address
        """
        listening_host = socket.gethostname()  # get the host name
        port = 0  # using 0 as our port, as this will make the library automatically choose avail. port

        listening_server = socket.socket()  # create instance of a socket
        try:
            listening_server.bind((listening_host, port))  # bind host and port together
        except socket.error as err:  # if the binding fails, we want to be notified
            print('Failed to bind listening_server: {}'.format(err))
            sys.exit(1)  # system should close because client can't receive messages

        # configure how many clients the server can listen to at once, I want 1000 b/c it's a nice number
        listening_server.listen(1000)
        listening_server.setblocking(False)
        self.selector.register(listening_server, selectors.EVENT_READ, self.accept_new_connection)

        return listening_server

    def accept_new_connection(self, new_mem):
        new_conn, new_addr = new_mem.accept()
        print('New connection with {} at address {}'.format(new_conn, new_addr))
        new_conn.setblocking(False)
        self.selector.register(new_conn, selectors.EVENT_READ, self.receive_msg)

        # populate the member_states dict with the members(key) and set their state (value) to WAITING
        for key in self.member_connections.keys():
            if key is not new_conn:  # if the new_connection is not in the list of members, we want to add it to our list
                self.member_connections = pickle.loads(new_conn.recv(self.BUF_SIZE))
            # Add the new_conn to the member_states dict with their state
            self.member_states[key] = State.WAITING_FOR_ANY_MESSAGE
            print('This {} was set to {}'.format(new_conn, self.member_states[key]))

    def receive_msg(self, member):
        message = pickle.loads(member.recv(self.BUF_SIZE))
        if message is None:
            print('No message received, closing connection: {}'.format(member))
            # set their state to default
            self.selector.unregister(member)
            member.close()
        elif message is 'ELECTION':
            print('election started')
        elif message is 'COORDINATOR':
            print('victor received')
        elif message is 'OK':
            print('OK received')

    def set_state(self, state, peer=None):
        """
        :return: the state that of my client
        """
        pass


class State(Enum):
    """
    Enumeration of states I can be in (copied from professor notes)
    """
    QUIESCENT = 'QUIESCENT'  # default state

    # Outgoing message is pending
    SEND_ELECTION = 'ELECTION'
    SEND_VICTORY = 'COORDINATOR'
    SEND_OK = 'OK'

    # Incoming message is pending
    WAITING_FOR_OK = 'WAIT_OK'  # When I've sent them an ELECTION message
    WAITING_FOR_VICTOR = 'WHO IS THE WINNER?'  # This one only applies to myself
    WAITING_FOR_ANY_MESSAGE = 'WAITING'  # When I've done an accept on their connect to my server

    def is_incoming(self):
        """
        Helper method to return fi the state is available to accept messages
        :return: True if the state is not in the list, else False
        """
        return self not in (State.SEND_ELECTION, State.SEND_VICTORY, State.SEND_OK)


if __name__ == '__main__':
    """
    Main function to run bully client program
    """
    if not 4 <= len(sys.argv) <= 5:
        print("Usage: python3 lab2.py GCDHOST GCDPORT SUID [DOB YYYY-MM-DD]")
        exit(1)

    if len(sys.argv) == 5:  # if we receive a dob, format it
        dob = sys.argv[4].split('-')
        curr_date = date.today()
        next_bd = date(curr_date.year, int(dob[1]), int(dob[2]))
        if next_bd < curr_date:
            next_bd = date(next_bd.year + 1, next_bd.month, next_bd.day)
    else:
        next_bd = date(2023, 1, 1)  # if no DOB is provided, set a default one

    print('Next Birthday: ', next_bd)
    suid = int(sys.argv[3])
    print('SU ID: ', suid)
    gcdHost = sys.argv[1]
    gcdPort = sys.argv[2]

    bully = BullyClient(gcdHost, gcdPort, next_bd, suid)
    bully.connect()
