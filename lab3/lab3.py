import sys

from fxp_bytes_subscriber import Subscriber

"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

NOTE FOR GRADERS: My Bellman-Ford algorithm is reporting losses, not true arbitrage. I have
exhausted my brain on this, and I'm not able to find where my error is. It may be possible
that I'm printing my path in reverse? 
"""

if __name__ == '__main__':
    """
    Main function to implementing the subscriber
    """
    if len(sys.argv) < 3:
        print('Usage: python3 lab3.py PUB_HOST PUB_PORT')
        exit(1)

    input_host = sys.argv[1]
    input_port = int(sys.argv[2])

    sub = Subscriber(input_host, input_port)
    sub.subscribe()
