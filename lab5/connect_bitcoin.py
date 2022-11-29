"""
Connects to a Bitcoin node using TPC/IP messages to retreive a block from the blockchain.
The block is obtained with getters and the transaction is printed from the block.

Author: Alicia Garcia
Date: 11/27/2022
"""
import socket
import time

from lab5 import bitcoin_interpreter as interpreter

BTC_IP = '47.40.67.209'
HOST_IP = '127.0.0.1'
PORT = 8333  # Mainnet
BUFF_SZ = 64000  # buffer size for socket
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
        peer_version_msg = exchange_messages(btc_sock, version_msg, expected_bytes=126)[0]


def get_build_msg(command, payload):
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


def version_message():
    """
    Build the version message payload per BTC protocol.
    Variables named after developer protocol
    :return: version message bytes
    """
    version = interpreter.int32_t(VERSION_NUM)  # version = 700015
    services = interpreter.uint64_t(0)  # Not a full node
    timestamp = interpreter.int64_t(int(time.time())) # current unix epoch
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





def exchange_messages(btc_sock: socket, send_msg: bytes, expected_bytes=None, height=None, wait=False):
    """
    Exchanges messages with BTC node and prints the message that are being sent and received
    :param btc_sock:       BTC socket
    :param send_msg:       bytes to send to BTC node
    :param expected_bytes: number of bytes expected to receive
    :param height:         local blockchain height
    :param wait:           Bool for whether to wait for a response
    :return:               list of message bytes
    """
    timeout = 0.5
    interpreter.print_message(send_msg, 'send', height)
    btc_sock.settimeout(timeout)
    recvd_bytes = b''
    address = (BTC_IP, PORT)

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
        recvc_message_list = split_msg(recvd_bytes)


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