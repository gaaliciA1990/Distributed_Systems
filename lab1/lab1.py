"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

Parameters:
    1. Connect to GCD with socket library (SOCK_STREAM)
    2. Test on port 23600 on host cs2.seattleu.edu
    3. Send message 'JOIN' using pickled bytes (dumps/load)
    4. Receive list of members in a dict with keys 'host' and 'port'
    5. Send message 'HELLO' to other members using pickled bytes.
    6. Connection timeout = 1500 ms. Handle timeout, failures.
    7. Return the response is a data structure that can be printed.
    8. Exit
"""

import socket
import pickle
import sys

timeout = float(1.500)
BUF_SZ = 1024
failedMsg = 'Failed to connect: '

"""
The simple client will make a connection to the Group Coordinator Daemon (GCD) and send a message
to JOIN and receive the data. Once the data is receive, the client will send a HELLO message
to each member of the server and print the response/error from each member before exiting.
"""


class SimpleClient:
    def __init__(self, argHost, argPort):
        self.host = argHost
        self.port = argPort

    #
    def connectToServer(self):
        # Set up connection with the server using a socket named sock
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            print('Contacting Server...\n')

            # Call the helper function to contact server and check response
            if self.contactServer(sock, self.host, self.port) is False:
                sys.exit(1)  # Exit the server with error

            # Send the JOIN message and receive the response in a variable
            sock.sendall(pickle.dumps('JOIN'))
            data = pickle.loads(sock.recv(BUF_SZ))  # De-serialize the response

            self.sendMsgToMember(data)

    def sendMsgToMember(self, data):
        # If we receive data (not null), send message to each member
        if data is not None:
            print(f'Connected with data!\n')
            # Loop through the data dict to send a message to each member of the group.
            for d in data:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mem:
                    # Call the helper function to contact server and check if false
                    if self.contactServer(mem, d.get('host'), d.get('port')) is False:
                        continue  # move on to the next server

                    # Send the HELLO message to the member, record the response, and print it
                    mem.send(pickle.dumps('HELLO'))
                    res = pickle.loads(mem.recv(BUF_SZ))  # De-serialize the response
                    print(repr(res))
            # exit the server successfully
            sys.exit(0)
        # If the data received is null/none, we want to exit the server with an error message
        else:
            print('Error: No data received\n')
            # exit the server with error
            sys.exit(1)

    # To remove duplicated code, this function will handle the connection checks. If connection failed,
    # return false, else true
    def contactServer(self, connection, host, port):
        # First try the connect, if failed, we display the message and exit
        try:
            connection.settimeout(timeout)
            connection.connect((host, port))
            return True
        except socket.timeout as to:
            print(failedMsg, repr(to))
            return False
        except OSError as err:
            print(failedMsg, repr(err))
            return False


# Main function to run client program
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 lab1.py HOST PORT")
        exit(1)
    inputHost = sys.argv[1]
    inputPort = int(sys.argv[2])

    client = SimpleClient(inputHost, inputPort)
    client.connectToServer()
