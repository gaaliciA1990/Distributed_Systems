"""
Connects to a Bitcoin node using TPC/IP messages to retreive a block from the blockchain.
The block is obtained with getters and the transaction is printed from the block.

Author: Alicia Garcia
Date: 11/27/2022
"""
import random
import socket
import sys
import time

from lab5 import bitcoin_interpreter as interpreter

'''
Test BTC IPs:
90.66.55.207
122.199.31.37
74.220.255.190
95.110.234.93
'''
BTC_IP = '95.110.234.93'
HOST_IP = '127.0.0.1'
PORT = 8333  # Mainnet
BUFF_SZ = 64000  # buffer size for socket
MAGIC_BYTES = bytes.fromhex('f9beb4d9')  # magic bytes
EMPTY_STRING = ''.encode()  # empty payload
COMMAND_SIZE = 12  # command msg length
VERSION_NUM = 70015  # highest protocol version, int32_t
BLOCK_NUM = 4112177 % 10000  # random block number
GENESIS = bytes.fromhex('000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')


def connect_to_btc(block_number: int):
    """
    Creates a TCP/IP connection with BTC and handles messages sent/received messages
    :param block_number: The block number to look for
    """
    btc_address = (BTC_IP, PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as btc_sock:
        btc_sock.connect(btc_address)

        # send version msg, get peer version msg
        peer_height = send_version_message(btc_sock)
        # Send verack to receive sendHeaders, sendcmpt, ping, addr, feefilter
        send_verack_message(btc_sock)
        # Send ping to receive pong
        send_ping_message(btc_sock)

        if block_number > peer_height:
            print('\nCould not retrieve block {}: max height is {}'.format(block_number, peer_height))
            sys.exit(1)

        block_hash = interpreter.swap_endian(GENESIS)
        curr_height = 0
        last_500_blocks = []  # to store last 500 blocks from inv messages

        # Send getblock until inventory has desired block number
        while curr_height < block_number:
            last_500_blocks, curr_height = send_getblocks_message(block_hash, curr_height, btc_sock)
            block_hash = last_500_blocks[-1]


def send_version_message(btc_sock: socket) -> int:
    """
    Sends version message and gets the peer height
    :param btc_sock:    BTC socket with our connection
    :return:            peer height
    """
    version_msg = get_message('version', version_message())
    peer_version_msg = exchange_messages(version_msg, btc_sock, expected_bytes=126)[0]

    return interpreter.unmarshal_uint(peer_version_msg[-5:-1])


def send_verack_message(btc_sock):
    """
    Sends a verack message and calls exchange messages to receive sendHeaders, sendcmp, ping,
    addr, and feefilter
    :param btc_sock: socket for BTC
    """
    verack_msg = get_message('verack', EMPTY_STRING)
    exchange_messages(verack_msg, btc_sock, expected_bytes=202)


def send_ping_message(btc_sock):
    """
    Sends a ping message and calls exchange message to receive pong
        :param btc_sock: socket for BTC

    """
    # get the ping payload per bitcoin protocol
    ping_msg = get_message('ping', interpreter.uint64_t(random.getrandbits(64)))
    exchange_messages(ping_msg, btc_sock, expected_bytes=32)


def get_message(command: str, payload: bytes) -> bytes:
    """
    Get the full message in bytes (header + payload)
    :param command: type of command/message
    :param payload: the payload of the message
    :return:        full message bytes
    """
    return build_msg_header(command, payload) + payload


def build_msg_header(command: str, payload: bytes) -> bytes:
    """
    Builds a BTC message header
    :param command: type of command/message
    :param payload: the payload of the message
    :return:        message header in bytes
    """
    command_name = command.encode('ascii')

    while len(command_name) < COMMAND_SIZE:
        command_name += b'\0'

    payload_size = interpreter.uint32_t(len(payload))
    check_sum = interpreter.checksum(payload)

    return b''.join([MAGIC_BYTES, command_name, payload_size, check_sum])


def get_data_message(txn_type, block_header) -> bytes:
    """
    Builds the getdata payload per the BTC protocol
    :param txn_type:    transaction type
    :param block_header: hash of the desired block
    :return:             message in bytes
    """
    count = interpreter.compactsize_t(1)
    entry_type = interpreter.uint32_t(txn_type)
    entry_hash = bytes.fromhex(block_header.hex())

    return count + entry_type + entry_hash


def getblocks_msg(header_hash) -> bytes:
    """
    Builds the getblock payload, per the BTC protocol
    :param header_hash:
    :return:
    """
    version = interpreter.uint32_t(VERSION_NUM)
    count = interpreter.compactsize_t(1)
    block_header_hash = bytes.fromhex(header_hash.hex())  # Assumes we passed in computed sha256(sha256(block)) hash
    max_hash = b'\0' * 32  # always ask for the max number of blocks

    return b''.join([version, count, block_header_hash, max_hash])


def version_message() -> bytes:
    """
    Build the version message payload per BTC protocol.
    Variables named after developer protocol
    :return: version message bytes
    """
    version = interpreter.int32_t(VERSION_NUM)  # version = 700015
    services = interpreter.uint64_t(0)  # Not a full node
    timestamp = interpreter.int64_t(int(time.time()))  # current unix epoch
    addr_recv_services = interpreter.uint64_t(1)  # full node
    addr_recv_ip_address = interpreter.ipv6_from_ipv4(BTC_IP)
    addr_recv_port = interpreter.uint16_t(PORT)
    addr_trans_services = interpreter.uint64_t(0)
    addr_trans_ip_address = interpreter.ipv6_from_ipv4(HOST_IP)
    addr_trans_port = interpreter.uint16_t(PORT)
    nonce = interpreter.uint64_t(0)
    user_agent_bytes = interpreter.compactsize_t(0)
    start_height = interpreter.int32_t(0)
    relay = interpreter.bool_t(False)

    return b''.join([version, services, timestamp,
                     addr_recv_services, addr_recv_ip_address, addr_recv_port,
                     addr_trans_services, addr_trans_ip_address, addr_trans_port,
                     nonce, user_agent_bytes, start_height, relay])


def exchange_messages(send_msg: bytes, btc_sock: socket, expected_bytes=None, height=None, wait=False) -> list:
    """
    Exchanges messages with BTC node and prints the message that are being sent and received
    :param btc_sock:       BTC socket
    :param send_msg:       bytes to send to BTC node
    :param expected_bytes: number of bytes expected to receive
    :param height:         local blockchain height
    :param wait:           Bool for whether to wait for a response
    :return:               list of message bytes
    """
    interpreter.print_message(send_msg, 'send', height)
    recvd_bytes = b''
    address = (BTC_IP, PORT)

    if btc_sock:
        btc_sock.settimeout(0.5)

    try:
        btc_sock.send(send_msg)
        if expected_bytes:
            # Fix the message size
            while len(recvd_bytes) < expected_bytes:
                recvd_bytes += btc_sock.recv(BUFF_SZ)
        elif wait:
            # wait until timeout to receive all bytes
            while True:
                recvd_bytes += btc_sock.recv(BUFF_SZ)

    except Exception as e:
        print('\nNo bytes left to receive from {}: {}'.format(address, str(e)))

    finally:
        print('\nReceived {} bytes from BTC node {}'.format(len(recvd_bytes), address))
        message_list = split_msg(recvd_bytes)  # Get the list of messages from of a member of the network

        for message in message_list:
            interpreter.print_message(message, 'receive', height)

        return message_list


def split_msg(peer_message: bytes) -> list:
    """
    Separates the bytes into a list of individual messages
    :param peer_message: message bytes to be split
    :return:            list of messages
    """
    message_list = []

    while peer_message:
        payload_size = interpreter.unmarshal_uint(peer_message[16:20])
        msg_size = interpreter.HDR_SZ + payload_size
        message_list.append(peer_message[:msg_size])
        peer_message = peer_message[msg_size:]  # move to the next section of data

    return message_list


@staticmethod
def send_getblocks_message(input_hash: bytes, height: int, btc_sock: socket) -> tuple:
    """
    Helper method for sending getblocks message to the BTC node.
    :param input_hash: locator hash for getblocks message
    :param height: current local blockchain height
    :return: tuple -> list of last 500 block headers, updated height
    """
    getblocks = get_message('getblocks', getblocks_msg(input_hash))
    peer_inv = exchange_messages(getblocks, btc_sock, expected_bytes=18027, height=height + 1)
    peer_inv_bytes = b''.join(peer_inv)
    last_500_headers = []

    for i in range(31, len(peer_inv_bytes), 36):
        last_500_headers = [peer_inv_bytes[i: i + 32]]

    try:
        height = height + (len(peer_inv[-1]) - 27) // 36
    except IndexError as ie:
        print(ie)

    return last_500_headers, height


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: connect_bitcoin.py [BLOCK NUMBER]: enter 0 to use default')
        sys.exit(1)

    if int(sys.argv[1]) != 0:
        block_num = int(sys.argv[1])
    else:
        block_num = BLOCK_NUM

    connect_to_btc(block_num)

    print('\nAll {} blocks have been retrieved!'.format(block_num))
    sys.exit(0)