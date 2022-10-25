"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

This class will:
1. subscribe to the forex publishing service,
2. for each message published, update a graph based on the published prices,
3. run Bellman-Ford, and
4. report any arbitrage opportunities.

Using UDP for this, so socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Connection is never open, so you need to tell the program who to send the message to

Published messages: <timestamp, currency 1, currency 2, exchange rate>
    - timestamp:  64-bit integer number of microseconds that have passed since 00:00:00 UTC on 1 January 1970 (excluding
    leap seconds). Sent in big-endian network format.
    - currency names: three-character ISO codes ('USD', 'GBP', 'EUR', etc.) transmitted in 8-bit ASCII from left to
    right.
    - exchange rate: 64-bit floating point number represented in IEEE 754 binary64 little-endian format.
"""
import ipaddress
import math
import socket
import sys
from array import array
from datetime import datetime
from bellman_ford import Arbitrage

PUBLISHER_ADD = ('localhost', 50403)
BUFF_SZ = 4096
MICROS_PER_SECOND = 1_000_000
SUBSCRIPTION_ENDED = 3  # If no msg received in 1 min time


class Subscriber:
    def __init__(self):
        self.subscr_sock, self.subscr_address = self.create_listening_server()
        self.timestamp_map = {}  # dictionary to hold the most recent entries for a currency group

    def subscribe(self):
        """
        This method is called to initiate the scubscription, listen on our
        listening server for incoming message, and run the arbitrage detection.
        If the timeout is reached, we exit the program.
        """
        subscriber = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        print('sending {!r} (even if no-one is listening)\n'.format(self.subscr_address))
        byte_msg = self.serialize_address(self.subscr_address)
        subscriber.sendto(byte_msg, PUBLISHER_ADD)

        while True:
            try:
                print('\nblocking, waiting to receive message')
                self.subscr_sock.settimeout(SUBSCRIPTION_ENDED)
                data = self.subscr_sock.recv(BUFF_SZ)
                decoded_data = self.decode_message(data, len(data))
                print(decoded_data)
                self.detect_arbitrage(decoded_data)
            except socket.timeout:
                print('No messages received after {} seconds. Closing program due to timeout.'.format(
                    SUBSCRIPTION_ENDED))
                sys.exit(0)  # break from the while loop to end program
            except OSError as err:
                print('Error ocurred: {}'.format(err))
                sys.exit(1)

    def decode_message(self, data, size) -> list:
        """
        Decode the message received by the publisher. This will determine how many messgaes are available
        in the byte data and pass those sections to helper methods for deserialization. Then this method
        will take the results of the deserialized portions and add them to a list.
        :param data: byte data gram from publisher
        :param size: the total number of bytes in the message
        :return: the decoded message in a list
        """
        total_msg = int(size / 32)  # the number of unique 32 byte messages in the data received
        decoded_msg = []
        print('there are {} messages to decode'.format(total_msg))

        # loop through the bytes based on the number of messages that exist
        for i in range(total_msg):
            start = i * 32
            end = (i + 1) * 32
            submessage = data[start:end]

            ts = submessage[0:8]  # set the timestamp (ts) range in bytes
            timestamp = self.deserialize_utcdatetime(ts)

            names = submessage[8:14]  # set the currency names range in bytes
            curr_names = self.deserialize_currency_name(names)

            price = submessage[14:22]  # set the exchange rate range in bytes
            exchg_rate = self.deserialize_price(price)

            # build our timestamp dictionary to keep track of messages received
            self.timestamp_map[curr_names] = timestamp
            # build our list of currencies and their exchange rates
            decoded_msg.append((curr_names, exchg_rate))

        return decoded_msg

    def create_listening_server(self) -> (socket, (str, int)):
        """
        Create a listening server to enable the subscription to the publisher
        :return: the socket and listening address
        """
        listener_addr = ('localhost', 0)  # set server address

        print('Starting up on {} on randomly chosen port\n'.format(*listener_addr))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind(listener_addr)  # bind the socket to the publishers address
        except socket.error as err:
            print('Failed to bind listening server: {}'.format(err))

        return sock, sock.getsockname()

    def serialize_address(self, msg: (str, int)) -> bytes:
        """
        Encode the subscription address to bytes to pass to the publisher
        :param msg: subscription address
        :return: encoded byte subscription address
        """
        ip = int(ipaddress.ip_address(msg[0])).to_bytes(4, 'big')
        port = msg[1].to_bytes(2, 'big')

        byte_list = [ip, port]
        byte_message = (b''.join(byte_list))
        return byte_message

    def deserialize_utcdatetime(self, ts: bytes) -> datetime:
        """
        This method converts the timestamp from bytes to date time.
        :param ts: bytes timestamp
        :return: datetime timestamp
        """
        timestamp = array('Q')
        timestamp.frombytes(ts)
        timestamp.byteswap()
        # converts the timestamp to seconds, then datetime based on timestamp method
        timestamp = datetime.fromtimestamp(int(timestamp[0] / MICROS_PER_SECOND))

        return timestamp

    def deserialize_currency_name(self, curr_names) -> tuple:
        """
        This method decodes the currency names and adds them to a tuple
        :param curr_names: the byte currencies that are being reported
        :return: tuple of currency str name
        """
        # convert the bytes to string into two currency string variables
        curr_a = curr_names[0:3].decode()
        curr_b = curr_names[3:6].decode()

        return curr_a, curr_b

    def deserialize_price(self, price) -> float:
        """
        This method converts the price exchange rate from bytes to a float
        :param price: bytes of price for a given message
        :return: the rate as a float
        """
        rate = array('d')
        rate.frombytes(price)
        rate = rate[0]

        return rate

    def detect_arbitrage(self, data):
        """
        This method will call the bellman_ford class to build a graph and add the nodes
        to the potential arbitrage path and will print the arbitrage path if it exists
        in paths
        :param data: decoded message with currencies and prices
        """
        paths = []
        arbitrage = Arbitrage(data)
        graph = arbitrage.build_graph()

        for key in graph:
            path = arbitrage.bellman_ford(graph, key)
            if path is None:
                continue
            if path not in paths:
                paths.append(path)

        for path in paths:
            if path is None:
                continue
            else:
                profit = 100  # set profit to 100 as a marker
                print('ARBITRAGE FOUND:\n')
                print('     Starting with {} {}\n'.format(path[0], profit))

                for index, value in enumerate(path):
                    if index + 1 < len(path):
                        start = path[index]
                        end = path[index + 1]
                        price = math.exp(-graph[start][end])
                        profit *= price
                        print('     {} to {} at {} --> {}\n'.format(start, end, price, profit))
