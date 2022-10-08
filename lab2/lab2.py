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


class BullyClient:
    def __init__(self, host, port, next_bday, su_id):
        self.listen_address = (host, int(port))

        days_to_bd = (next_bday - date.today()).days  # determine the number of days till their next bday
        self.process_id = (days_to_bd, su_id)

        self.members = {}  # creating tuple for holding connected members
        self.states = {}  # creating tuple for holding member states
        self.leader = None  # election pending as indicated by None
        self.selector = selectors.DefaultSelector()

        # self.listener, self.listener_address = self.start_a_server()

        self.BUF_SIZE = 1024
        self.timeout = float(1.500)
        self.failed_msg = 'Failed to connect: '

    def connect(self):
        # Set up connection with the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print('Contacting GCD Server...\n')
            # check we connect to the server successfully
            if self.contact_server(sock, self.listen_address[0], self.listen_address[1]) is False:
                sys.exit(1)

            print('Successfully connected to GCD Server...\n')
            join_msg= ('JOIN', (self.process_id, self.listen_address))
            sock.sendall(pickle.dumps(join_msg))
            self.members = pickle.loads(sock.recv(self.BUF_SIZE))
            print(self.members)

    # This function will handle the connection checks. If connection failed, return false
    # else true
    def contact_server(self, connection, host, port):
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

    """
    Creating a static self server to handle messages sent to my client
    """
    @staticmethod
    def create_server(self):




# Main function to run bully client program
if __name__ == '__main__':
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

    exit(0)
