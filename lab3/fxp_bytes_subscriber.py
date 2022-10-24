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
import socket
from array import array
from datetime import datetime

PUBLISHER_ADD = ('localhost', 50403)
BUFF_SZ = 4096
MICROS_PER_SECOND = 1_000_000


class Subscriber:
    def __init__(self):
        self.subscr_sock, self.subscr_address = self.create_listening_server()

    def subscribe(self):
        subscriber = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(subscriber)

        print('sending {!r} (even if no-one is listening)\n'.format(self.subscr_address))
        byte_msg = self.serialize_address(self.subscr_address)
        subscriber.sendto(byte_msg, PUBLISHER_ADD)

        while True:
            print('\nblocking, waiting to receive message')
            data = self.subscr_sock.recv(BUFF_SZ)
            self.decode_message(data, len(data))

    def decode_message(self, data, size):
        """
        Decode the message received by the publisher. This will determine how many messgaes are available
        in the byte data and pass those sections to helper methods for deserialization. Then this method
        will take the results of the deserialized portions and add them to a list.
        :param data: byte data gram from publisher
        :param size: the total number of bytes in the message
        :return: the decoded message in a list
        """
        total_msg = int(size / 32)  # the number of unique 32 byte messages in the data received
        print('there are {} messages to decode'.format(total_msg))

        # loop through the bytes based on the number of messages that exist
        for i in range(total_msg):
            start = i * 32
            end = (i + 1) * 32
            submessage = data[start:end]

            ts = submessage[0:8]  # set the timestamp (ts) range in bytes
            timestamp = self.deserialize_utcdatetime(ts)

            names = submessage[8:14] # set the currency names range in bytes
            self.deserialize_currency_name(names)

            ex_rate = submessage[14:22]  # set the exchange rate range in bytes
            self.deserialize_exchange_rate(ex_rate)

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

        print(str(timestamp))
        return timestamp

    def deserialize_currency_name(self, curr_names):
        pass

    def deserialize_exchange_rate(self, exchange_rate):
        pass
