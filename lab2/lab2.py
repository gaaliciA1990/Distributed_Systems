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


class BullyClient:
    def __init__(self):
        pass


# Main function to run bully client program
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 lab1.py HOST PORT")
        exit(1)
