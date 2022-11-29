"""
Connects to a Bitcoin node using TPC/IP messages to retreive a block from the blockchain.
The block is obtained with getters and the transaction is printed from the block.

Author: Alicia Garcia
Date: 11/27/2022
"""
import socket
import time

from lab5 import bitcoin_interpreter

BTC_IP = '47.40.67.209'
HOST_IP = '127.0.0.1'
PORT = 8333  # Mainnet
MAGIC_BYTES = bytes.fromhex('f9beb4d9')  # magic bytes
EMPTY_STRING = ''.encode()  # empty payload
COMMAND_SIZE = 12  # command msg length
VERSION_NUM = 70015  # highest protocol version, int32_t
BLOCK_NUM = 4112177 % 10000  # random block number


def connect_to_btc():
    btc_address = (BTC_IP, PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as btc_sock:
        btc_sock.connect(btc_address)

        # send version msg, get peer version msg
        version_msg = get_build_msg('version', version_message())
        peer_version_msg = exchange_messages(version_msg, expected_bytes=126)[0]


def get_build_msg(command, payload):
    """
    Get the full message in bytes (header + payload)
    :param command: type of command/message
    :param payload: the payload of the message
    :return:        full message bytes
    """
    return build_msg_header(command, payload) + payload


def build_msg_header(command, payload):
    """
    Builds a BTC message header
    :param command: type of command/message
    :param payload: the payload of the message
    :return:        message header in bytes
    """
    command_name = command.encode('ascii')

    while len(command_name) < COMMAND_SIZE:
        command_name += b'\0'

    payload_size = bitcoin_interpreter.uint32_t(len(payload))
    check_sum = bitcoin_interpreter.checksum(payload)

    return b''.join([MAGIC_BYTES, command_name, payload_size, check_sum])


def version_message():
    """
    Build the version message payload per BTC protocol.
    Variables named after developer protocol
    :return: version message bytes
    """
    version = bitcoin_interpreter.int32_t(VERSION_NUM)  # version = 700015
    services = bitcoin_interpreter.uint64_t(0)  # Not a full node
    timestamp = bitcoin_interpreter.int64_t(int(time.time())) # current unix epoch
    addr_recv_services = bitcoin_interpreter.uint64_t(1)  # full node
    addr_recv_ip_address = bitcoin_interpreter.ipv6_from_ipv4(BTC_IP)
    addr_recv_port = bitcoin_interpreter.uint16_t(PORT)
    addr_trans_services = bitcoin_interpreter.uint64_t(0)
    addr_trans_ip_address = bitcoin_interpreter.ipv6_from_ipv4(HOST_IP)
    addr_trans_port = bitcoin_interpreter.uint16_t(PORT)
    nonce = bitcoin_interpreter.uint64_t(0)
    user_agent_bytes = bitcoin_interpreter.compactsize_t(0)
    start_height = bitcoin_interpreter.int32_t(0)
    relay = bitcoin_interpreter.bool_t(False)

    return b''.join([version, services, timestamp,
                     addr_recv_services, addr_recv_ip_address, addr_recv_port,
                     addr_trans_services, addr_trans_ip_address, addr_trans_port,
                     nonce, user_agent_bytes, start_height, relay])


def exchange_messages(send_msg, expected_bytes=None, height=None, wait=False):
    """
    Exchanges messages with BTC node and prints the message that are being sent and received
    :param send_msg:       bytes to send to BTC node
    :param expected_bytes: number of bytes expected to receive
    :param height:         local blockchain height
    :param wait:           Bool for whether to wait for a response
    :return:                list of message bytes
    """
    pri