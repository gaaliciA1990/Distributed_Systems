"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

Requirements:
    1. Have an identity which is the pair: (days until your next birthday, your SU ID)
    2. JOIN the group by communicating with GCD (lab1)
    3. Participate in elections
    4. Identify when leader is not present and initiate an election (EC)
    5. Pretend to fail every so often and subsequently recover

# The "least" of two identities is the one with fewer days until the birthday, or if they have the same birthday, then
the one with the smaller SU ID.

# A process listens for other members wanting to send messages to it.

# A process connects to each higher process by sending an ELECTION message to the higher process's listening server as
described in the message protocol below.

# Detecting a failed leader is done by each process sending occasional PROBE messages to her.

# All messages are pickled and are a pair (message_name, message_data), where message_name is the text of the message
name (that is, one of 'JOIN', 'ELECTION', 'COORDINATOR', or 'PROBE') and the message_data is specified in the protocol
below or, if there is no message data, use None. Message responses, when they exist, can either be just pickled text or
data as specified in the protocol below.

# Sockets are not re-used. Once a message and its response, if it has one, are finished, the socket is closed. (For a
commercial application, we would want to keep the sockets to avoid the reconnection overhead.)

# Create your listening server with address ('localhost', 0) and then use listener.getsockname() to report your listener
to the GCD when joining the group. The 'localhost' host name is special and usually translates to 127.0.0.1 and the port
number of zero asks the socket library to allocate any free port for you.

# Peer sockets must be non-blocking, i.e. you mustn't block waiting for the receipt of the OK when sending an ELECTION
message (think about why this would cause our peers to think we had failed). Instead you need to poll for the response
in conjunction with everything else you are simultaneously doing. It is recommended that you use socket.select() to do
this.
"""

import socket
import pickle
import sys


class BullyClient:
    def __init__(self):
        pass


# Main function to run bully client program
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 lab1.py HOST PORT")
        exit(1)
