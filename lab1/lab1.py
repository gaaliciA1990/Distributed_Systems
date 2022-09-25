"""
Lab1 - Simple Client in a Client-Server System
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
# Todo: Set connection timeout!

import socket
import pickle
import sys

HOST = "cs2.seattleu.edu"
PORT = 23600

# Set up connection with the server using a socket named sock
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # First try the connect, if failed, we display the message and exit
    try:
        sock.connect((HOST, PORT))
    except OSError as msg:
        print('Could Not Connect To Host!')
        sys.exit(1)  # Exit the server with error

    # Send the JOIN message and receive the response in a variable
    sock.sendall(pickle.dumps('JOIN'))
    data = pickle.load(sock.recv(1024))  # De-serialize the response

    # If we receive data (not null), start talking to each member
    if data is not None:
        print(f'Connected!')
        # Loop through the data dict to send a message to each member of the group. Need to create a new socket connection
        # which is named mem (member)
        for d in data:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mem:
                # Try to make the connect to the host, if an error occurs, print message and continue to next member
                try:
                    mem.connect(d.host, d.port)
                except OSError as msg:
                    print('Failed to connect to host: ', repr(d.host))
                    continue

                # Send the HELLO message to the member, record the response, and print it
                mem.send(pickle.dumps('HELLO'))
                res = pickle.load(mem.recv(1024))  # De-serialize the response
                print('OK', repr(res))
        # exit the server successfully
        sys.exit(0)
    # If the data received is null/none, we want to exit the server with an error message
    else:
        print('Error: No data received')
        # exit the server with error
        sys.exit(1)
