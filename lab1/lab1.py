# Lab1 - Simple Client in a Client-Server System
# Parameters:
#    1. Connect to GCD with socket library (SOCK_STREAM)
#    2. Test on port 23600 on host cs2.seattleu.edu
#    3. Send message 'JOIN' using pickled bytes (dumps/load)
#    4. Receive list of members in a dict with keys 'host' and 'port'
#    5. Send message 'HELLO' to other members using pickled bytes.
#    6. Connection timeout = 1500 ms. Handle timeout, failures.
#    7. Return the response is a data structure that can be printed.
#    8. Exit

import socket
import pickle
import sys

HOST = 'cs2.seattleu.edu'
PORT = 23600
timeout = float(1.500)
BUF_SZ = 1024
failedMsg = 'Failed to connect: '


def simpleClient():
    # Set up connection with the server using a socket named sock
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print('Contacting Server...\n')
        # Call the helper function to contact server
        contactServer(sock, HOST, PORT)

        # Send the JOIN message and receive the response in a variable
        sock.sendall(pickle.dumps('JOIN'))
        data = pickle.loads(sock.recv(BUF_SZ))  # De-serialize the response

        # If we receive data (not null), start talking to each member
        if data is not None:
            print(f'Connected with data!\n')
            # Loop through the data dict to send a message to each member of the group. Need to create a new socket connection
            # which is named mem (member)
            for d in data:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mem:
                    # Call the helper function to contact server
                    contactServer(mem, d.get('host'), d.get('port'))

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


# To remove duplicated code, this function will handle the connection checks
def contactServer(connection, host, port):
    # First try the connect, if failed, we display the message and exit
    try:
        connection.settimeout(timeout)
        connection.connect((host, port))
    except socket.timeout as to:
        print(failedMsg, repr(to))
        sys.exit(1)  # Exit the server with error
    except OSError as err:
        print(failedMsg, repr(err))
        sys.exit(1)  # Exit the server with error


# Main function to run client program
if __name__ == '__main__':
    simpleClient()
