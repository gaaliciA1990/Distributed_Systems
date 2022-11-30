"""
Module for serializing and deserializing bytes in order
to construct messages per Bitcoins messaging protocol

Author: Alicia Garcia (copied from lab5 provided code, enhanced where needed)
Date: 11/27/2022
"""
from time import strftime, gmtime
from hashlib import sha256

HDR_SZ = 24
SPACES = '    '


def compactsize_t(n: int) -> bytes:
    """
    Marshalls data type of compactsize
    :param n: integer value
    :return:  marshalled compactsize integer
    """
    if n < 252:
        return uint8_t(n)
    if n < 0xffff:
        return uint8_t(0xfd) + uint16_t(n)
    if n < 0xffffffff:
        return uint8_t(0xfe) + uint32_t(n)
    return uint8_t(0xff) + uint64_t(n)


def unmarshal_compactsize(b: bytes) -> tuple:
    """
    Unmarshalls compactsize data type
    :param b: bytes
    :return:  raw bytes of the integer
    """
    key = b[0]
    if key == 0xff:
        return b[0:9], unmarshal_uint(b[1:9])
    if key == 0xfe:
        return b[0:5], unmarshal_uint(b[1:5])
    if key == 0xfd:
        return b[0:3], unmarshal_uint(b[1:3])
    return b[0:1], unmarshal_uint(b[0:1])


def bool_t(flag: bool) -> bytes:
    """
    Marshalls boolean to unsigned 8 bit
    :param flag: boolean flag
    :return:     unsigned int
    """
    return uint8_t(1 if flag else 0)


def ipv6_from_ipv4(ipv4_str: str) -> bytes:
    """
    Marshalls ipv4 string to ipv6 bytes
    :param ipv4_str: string to convert
    :return:         ipv6 bytes
    """
    pchIPv4 = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0xff, 0xff])
    return pchIPv4 + bytearray((int(x) for x in ipv4_str.split('.')))


def ipv6_to_ipv4(ipv6: bytes) -> str:
    """
    Unmarshalls ipv6 byte to ipv4 string
    :param ipv6: byte to convert
    :return:     ipv4 string
    """
    return '.'.join([str(b) for b in ipv6[12:]])


def uint8_t(n: int) -> bytes:
    """
    Unmarshalls unsigned integer to 8 bit integer
    :param n: unsigned int
    :return:  8 bit int
    """
    return int(n).to_bytes(1, byteorder='little', signed=False)


def uint16_t(n: int) -> bytes:
    """
    Unmarshalls unsigned integer to 16 bit integer
    :param n:  unsigned int
    :return:   16 bit int
    """
    return int(n).to_bytes(2, byteorder='little', signed=False)


def int32_t(n: int) -> bytes:
    """
    Marshalls 32 bit integer to unsigned
    :param n: 32 bit int
    :return:  unsigned int
    """
    return int(n).to_bytes(4, byteorder='little', signed=True)


def uint32_t(n: int) -> bytes:
    """
    Unmarshalls unsigned integer to 32 bit int
    :param n:   unsiged integer
    :return:    32 bit int
    """
    return int(n).to_bytes(4, byteorder='little', signed=False)


def int64_t(n: int) -> bytes:
    """
    Marshalls 64 bit integer to unsigned
    :param n: 64 bit integer
    :return: unsigned int
    """
    return int(n).to_bytes(8, byteorder='little', signed=True)


def uint64_t(n: int) -> bytes:
    """
    Unmarshalls unsigned integer to 64 bit int
    :param n: unsigned int
    :return:  64 bit int
    """
    return int(n).to_bytes(8, byteorder='little', signed=False)


def unmarshal_int(b: bytes) -> int:
    """
    Unmarshalls signed integer
    :param b: signed int
    :return:  int
    """
    return int.from_bytes(b, byteorder='little', signed=True)


def unmarshal_uint(b: bytes) -> int:
    """
    Unmarshalls unsigned integer
    :param b: unsigned int
    :return:  int
    """
    return int.from_bytes(b, byteorder='little', signed=False)


def checksum(payload: bytes) -> bytes:
    """
    Calculate bitcoin protocol checksum using sha256.
    :param payload: payload bytes
    :return:    first 4 bytes of checksum
    """
    return custom_hash(payload)[:4]


def swap_endian(b: bytes) -> bytes:
    """
    Swap the endianness of the given bytes. If little, swaps to big. If big,
    swaps to little.
    :param b: bytes to swap
    :return: swapped bytes
    """
    swapped = bytearray.fromhex(b.hex())
    swapped.reverse()
    return swapped


def print_message(msg: bytes, text=None, height=None) -> str:
    """
    Report the contents of the given bitcoin message
    :param msg: bitcoin message including header
    :param text:  Message string, optional
    :param height: height of the local blockchain, optional
    :return: message type string
    """
    print('\n{}MESSAGE'.format('' if text is None else (text + ' ')))

    print('({}) {}'.format(len(msg), msg[:60].hex() + ('' if len(msg) < 60 else '...')))

    payload = msg[HDR_SZ:]
    command = print_header(msg[:HDR_SZ], checksum(payload))

    if payload:
        if command == 'block':
            header_hash = swap_endian(custom_hash(payload[:80])).hex()
        else:
            header_hash = ''
        print('{}{} {}'.format(SPACES, command.upper(), header_hash))
        print(SPACES + '-' * 56)

    if command == 'version':
        print_version_msg(payload)
    elif command == 'sendcmpct':
        print_sendcmpct_message(payload)
    elif command == 'ping' or command == 'pong':
        print_ping_pong_message(payload)
    elif command == 'addr':
        print_addr_message(payload)
    elif command == 'feefilter':
        print_feefilter_message(payload)
    elif command == 'getblocks':
        print_getblocks_message(payload)
    elif command == 'block':
        print_block_message(payload)
    elif command == 'inv' or command == 'getdata' or command == 'notfound':
        print_inv_message(payload, height)

    return command


def print_block_message(payload):
    """
    Prints the block message
    :param payload: block message
    """
    # block headers
    version = payload[:4]
    prev_block = payload[4:36]
    merkle_root = payload[36:68]
    epoch_time = payload[68:72]
    bits = payload[72:76]
    nonce = payload[76:80]

    block_count_bytes, block_count = unmarshal_compactsize(payload[80:])
    transactions = payload[80 + len(block_count_bytes):]
    prev_hash = swap_endian(prev_block)
    merkle_hash = swap_endian(merkle_root)
    time_str = gmtime(unmarshal_int(epoch_time))

    print('{}{:32} version: {}'.format(SPACES, version.hex(), unmarshal_int(version), SPACES))
    print("{}{:32}\n{}{:32} previous block hash\n{}".format(SPACES, prev_hash.hex()[:32], SPACES, prev_hash.hex()[32:],
                                                            SPACES))
    print(
        '{}{:32}\n{}{:32} merkle root hash\n{}-'.format(SPACES, merkle_hash.hex()[:32], SPACES, merkle_hash.hex()[32:],
                                                        SPACES))
    print('{}{:32} epoch time: {}'.format(SPACES, epoch_time.hex(), time_str))
    print('{}{:32} bits: {}'.format(SPACES, bits.hex(), unmarshal_uint(bits)))
    print('{}{:32} nonce: {}'.format(SPACES, nonce.hex(), unmarshal_uint(nonce)))
    print('{}{:32} transaction count: {}'.format(SPACES, block_count_bytes.hex(), block_count))

    print_transaction(transactions)


def print_inv_message(payload, height):
    """
    Prints the inv message
    :param payload: inv message
    :param height:  local blockchaing height
    """
    inv_bytes, inv = unmarshal_compactsize(payload)
    val = len(inv_bytes)
    inventory = []

    for _ in range(inv):
        entry = payload[val:val + 4], payload[val + 4: val + 36]
        inventory.append(entry)
        val += 36

    print('{}{:32} inv count: {}'.format(SPACES, inv_bytes.hex(), inv))

    for val, (tx_type, tx_hash) in enumerate(inventory, start=height if height else 1):
        print('\n{}{:32} type: {}\n{}-'.format(SPACES, tx_type.hex(), unmarshal_uint(tx_type), SPACES))
        block_hash = swap_endian(tx_hash).hex()
        print('{}{:32}\n{}{:32} block #{} hash'.format(SPACES, block_hash[:32], SPACES, block_hash[32:], val))


def print_getblocks_message(payload):
    """
    Print the contents of the getblocks message
    :param payload: getblocks message
    """
    version = payload[:4]
    getblocks_bytes, getblocks_count = unmarshal_compactsize(payload[4:])
    val = 4 + len(getblocks_bytes)
    block_header_hashes = []

    for _ in range(getblocks_count):
        block_header_hashes.append(payload[val:val + 32])
        val += 32

    end_hash = payload[val:]

    print('{}{:32} version: {}'.format(SPACES, version.hex(), unmarshal_uint(version)))
    print('{}{:32} hash count: {}'.format(SPACES, getblocks_bytes.hex(), getblocks_count))

    for header in block_header_hashes:
        hash_hex = swap_endian(header).hex()
        print('\n{}{:32}\n{}{:32} block header hash # {}: {}'.format(SPACES, hash_hex[:32], SPACES, hash_hex[32:], 1,
                                                                     unmarshal_uint(header)))

    end_hash_hex = end_hash.hex()

    print('\n{}{:32}\n{}{:32} stop hash: {}'.format(SPACES, end_hash_hex[:32], SPACES, end_hash_hex[32:],
                                                    unmarshal_uint(end_hash)))


def print_feefilter_message(feerate):
    """
    Prints the contents of the feefilter message.
    :param feerate: feefilter message
    """
    print('{}{:32} count: {}'.format(SPACES, feerate.hex(), unmarshal_uint(feerate)))


def print_addr_message(payload):
    """
    Prints contects of the address message
    :param payload: address message to print
    """
    address_bytes, address_count = unmarshal_compactsize(payload)
    val = len(address_bytes)

    epoch_time = payload[val:val + 4]  # extract the time from the data in ip_count
    services = payload[val + 4:val + 12]  # extract the services info from the data in ip_count
    ip_address = payload[val + 12:val + 28]  # extract the IP address from the data in ip_count
    port = payload[val + 28:]  # extract the port from the data in ip_count

    time_str = gmtime(unmarshal_int(epoch_time))

    print('{}{:32} count: {}'.format(SPACES, address_bytes.hex(), address_count))
    print('{}{:32} epoch time: {}'.format(SPACES, epoch_time.hex(), time_str))
    print('{}{:32} services: {}'.format(SPACES, services.hex(), unmarshal_uint(services)))
    print('{}{:32} host: {}'.format(SPACES, ip_address.hex(), ipv6_to_ipv4(ip_address)))
    print('{}{:32} port: {}'.format(SPACES, port.hex(), unmarshal_uint(port)))


def print_ping_pong_message(nonce):
    """
    Prints contnets of ping/pong message
    :param nonce:  Payload that is always nonce
    """
    print('{}{:32} nonce: {}'.format(SPACES, nonce.hex(), unmarshal_uint(nonce)))


def print_sendcmpct_message(payload):
    """
    Prints contents of the sendcmpct message.
    :param payload: sendcmpct message payload
    """
    announce = payload[:1]
    version = payload[1:]

    print('{}{:32} announce: {}'.format(SPACES, announce.hex(), bytes(announce) != b'\0'))
    print('{}{:32} version: {}'.format(SPACES, version.hex(), unmarshal_uint(version)))


def print_version_msg(b):
    """
    Report the contents of the given bitcoin version message (sans the header)
    :param b: version message contents
    """
    # pull out fields
    version = b[:4]
    my_services = b[4:12]
    epoch_time = b[12:20]
    your_services = b[20:28]

    rec_host = b[28:44]
    rec_port = b[44:46]
    my_services2 = b[46:54]
    my_host = b[54:70]
    my_port = b[70:72]
    nonce = b[72:80]

    user_agent_size, uasz = unmarshal_compactsize(b[80:])
    i = 80 + len(user_agent_size)
    user_agent = b[i:i + uasz]
    i += uasz
    start_height, relay = b[i:i + 4], b[i + 4:i + 5]
    extra = b[i + 5:]

    # print report
    prefix = SPACES

    print(prefix + 'VERSION')
    print(prefix + '-' * 56)

    print('{}{:32} version {}'.format(prefix, version.hex(), unmarshal_int(version)))
    print('{}{:32} my services'.format(prefix, my_services.hex()))

    time_str = strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime(unmarshal_int(epoch_time)))

    print('{}{:32} epoch time {}'.format(prefix, epoch_time.hex(), time_str))
    print('{}{:32} your services'.format(prefix, your_services.hex()))
    print('{}{:32} your host {}'.format(prefix, rec_host.hex(), ipv6_to_ipv4(rec_host)))
    print('{}{:32} your port {}'.format(prefix, rec_port.hex(), unmarshal_uint(rec_port)))
    print('{}{:32} my services (again)'.format(prefix, my_services2.hex()))
    print('{}{:32} my host {}'.format(prefix, my_host.hex(), ipv6_to_ipv4(my_host)))
    print('{}{:32} my port {}'.format(prefix, my_port.hex(), unmarshal_uint(my_port)))
    print('{}{:32} nonce'.format(prefix, nonce.hex()))
    print('{}{:32} user agent size {}'.format(prefix, user_agent_size.hex(), uasz))
    print('{}{:32} user agent \'{}\''.format(prefix, user_agent.hex(), str(user_agent, encoding='utf-8')))
    print('{}{:32} start height {}'.format(prefix, start_height.hex(), unmarshal_uint(start_height)))
    print('{}{:32} relay {}'.format(prefix, relay.hex(), bytes(relay) != b'\0'))

    if len(extra) > 0:
        print('{}{:32} EXTRA!!'.format(prefix, extra.hex()))


def print_header(header, expected_cksum=None) -> str:
    """
    Report the contents of the given bitcoin message header
    :param header: bitcoin message header (bytes or bytearray)
    :param expected_cksum: the expected checksum for this version message, if known
    :return: message type
    """
    magic = header[:4]
    command_hex = header[4:16]
    payload_size = header[16:20]
    cksum = header[20:]

    command = str(bytearray([b for b in command_hex if b != 0]), encoding='utf-8')
    psz = unmarshal_uint(payload_size)

    if expected_cksum is None:
        verified = ''
    elif expected_cksum == cksum:
        verified = '(verified)'
    else:
        verified = '(WRONG!! ' + expected_cksum.hex() + ')'

    prefix = SPACES

    print(prefix + 'HEADER')
    print(prefix + '-' * 56)
    print('{}{:32} magic'.format(prefix, magic.hex()))
    print('{}{:32} command: {}'.format(prefix, command_hex.hex(), command))
    print('{}{:32} payload size: {}'.format(prefix, payload_size.hex(), psz))
    print('{}{:32} checksum {}'.format(prefix, cksum.hex(), verified))

    return command


def print_transaction(txn):
    """
    Prints the transaction content of a block
    :param txn: transaction bytes from the block
    """
    # Parse the version adn transaction input count bytes
    version = txn[:4]
    txn_count_bytes, txn_count = unmarshal_compactsize(txn[4:])
    val = 4 + len(txn_count_bytes)

    # Parse coinbase bytes
    coinbase_txn, coinbase_bytes_count = parse_coinbase(txn[val:], version)
    txn_in_list = [(coinbase_txn, coinbase_bytes_count)]
    val += len(b''.join(coinbase_txn))

    # Parse transaction input bytes
    for _ in range(1, txn_count):
        txn_in, script_bytes_count = parse_transaction_in(txn[val:])
        txn_in_list.append((txn_in, script_bytes_count))
        val += len(b''.join(txn_in))

    # Parse transaction output count in bytes
    txn_out_bytes, txn_out_count = unmarshal_compactsize(txn[val:])
    txn_out_list = []
    val += len(txn_out_bytes)

    # Parse transaction output bytes
    for _ in range(txn_out_count):
        txn_out, pk_script_count = parse_txn_out(txn[val:])
        txn_out_list.append((txn_out, pk_script_count))
        val += len(b''.join(txn_out))

    lock_time = txn[val: val + 4]

    print('{}{:32} version: {}'.format(SPACES, version.hex(), unmarshal_uint(version)))

    print('\n{}Transaction Inputs:'.format(SPACES))
    print(SPACES + '-' * 32)
    print('{}{:32} input txn count: {}'.format(SPACES, txn_count_bytes.hex(), txn_count))
    print_transaction_inputs(txn_in_list)

    print('\n{}Transaction Outputs:'.format(SPACES))
    print(SPACES + '-' * 32)
    print('{}{:32} output txn count: {}'.format(SPACES, txn_out_bytes.hex(), txn_out_count))
    print_transaction_outputs(txn_out_list)

    print('{}{:32} lock time: {}'.format(SPACES, lock_time.hex(), unmarshal_uint(lock_time)))
    if txn[val + 4:]:
        print('EXTRA: {}'.format(txn[val + 4:].hex()))


@staticmethod
def parse_coinbase(cb_bytes, version) -> tuple:
    """
    Helper method that parses the bytes of a coinbase transaction
    :param cb_bytes: coinbase transaction bytes
    :param version:  version number of the block
    :return:         list of the coinbase bytes, number of bytes in the script
    """
    hash_null = cb_bytes[:32]
    index = cb_bytes[32:36]
    script, script_count = unmarshal_compactsize(cb_bytes[36:])
    val = 36 + len(script)

    height = None
    # Version 1 doesn't require height param for block [227:836]
    if unmarshal_uint(version) > 1:
        height = cb_bytes[val:val + 4]
        val += 4

    cb_script = cb_bytes[val:val + script_count]
    sequence = cb_bytes[val + script_count: val + script_count + 4]

    if height:
        return [hash_null, index, script, height, cb_script, sequence], script_count
    else:
        return [hash_null, index, script, cb_script, sequence], script_count


@staticmethod
def parse_transaction_in(txn_in) -> tuple:
    """
    Helper method to parse the transaction input bytes from a transaction
    :param txn_in: transaction input bytes
    :return:       tuple -> list of the transaction in bytes, number of bytes in the script
    """
    value = txn_in[:32]
    index = txn_in[32:36]
    script, script_count = unmarshal_compactsize(txn_in[36:])
    val = 36 + len(script)
    sig_script = txn_in[val:val + script_count]
    sequence = txn_in[val + script_count:]

    return [value, index, script, sig_script, sequence], script_count


@staticmethod
def parse_txn_out(txn_out) -> tuple:
    """
    Helper method to parse the transaction output bytes of a transaction
    :param txn_out: transaction output bytes
    :return:        tuple -> list of the transaction out bytes, number of bytes in the script
    """
    value = txn_out[:8]
    pk_script, pk_script_count = unmarshal_compactsize(txn_out[:8:])
    val = 8 + len(pk_script)
    pk = txn_out[val: val + pk_script_count]

    return [value, pk_script, pk], pk_script_count


@staticmethod
def print_transaction_inputs(txn_in_list):
    """
    Helper method to print the transaction inputs from the transaction portion of the block
    :param txn_in_list: list of input transactions
    """
    for i, txn_in in enumerate(txn_in_list, start=1):
        print('\n{}Transaction {}{}:'.format(SPACES, i, ' (Coinbase)' if i == 1 else ''))
        print(SPACES + '*' * 32)

        value, index, script, sig_script, seq = txn_in[0]
        script_count = txn_in[1]

        print('{}{:32}\n{}{:32} hash\n{}-'.format(SPACES, value.hex()[:32], SPACES, value.hex()[32:], SPACES))
        print('{}{:32} index: {}'.format(SPACES, index.hex(), unmarshal_uint(index)))
        print('{}{:32} script bytes: {}'.format(SPACES, script.hex(), script_count))

        if i == 1:
            print('{}{:32} {}script'.format(SPACES, sig_script.hex(), 'coinbase '))
        else:
            print('{}{:32} script'.format(SPACES, sig_script.hex()))

        print('{}{:32} sequence number'.format(SPACES, seq.hex()))


@staticmethod
def print_transaction_outputs(txn_out_list):
    """
    Helper method to print the transaction outputs from the transaction portion of the block
    :param txn_out_list: list of output transactions
    """
    for i, txn_out in enumerate(txn_out_list, start=1):
        print('\n{}Transaction {}:'.format(SPACES, i))
        print(SPACES + '*' * 32)

        value, pk_script, pk = txn_out[0]
        pk_script_count = txn_out[1]

        satoshis = unmarshal_uint(value)
        btc = convert_to_sat(satoshis)

        print('{}{:32} value: {} satoshis = {} BTC'.format(SPACES, value.hex(), satoshis, btc))
        print('{}{:32} public key script length: {}\n{}-'.format(SPACES, pk_script.hex(), pk_script_count, SPACES))

        for j in range(0, pk_script_count * 2, 32):
            if j + 32 > pk_script_count * 2:
                # we have the PK, so we want to print it
                print('{}{:32}{}'.format(SPACES, pk.hex()[j:j + 32], ' public key script\n{}-'.format(SPACES)))
            else:
                # we don't have PK, so we don't print it
                print('{}{:32}'.format(SPACES, pk.hex()[j:j + 32]))


@staticmethod
def convert_to_sat(btc) -> int:
    """
    Converts BTC to Satoshis currency
    :param btc:  bitcoint value
    :return:    satoshi value
    """
    return btc * 10e5


@staticmethod
def custom_hash(payload: bytes) -> bytes:
    """
    Uses sha256 to hash the payload, per BTC protocol
    :param payload: payload message
    :return:        hashed bytes
    """
    return sha256(sha256(payload).digest()).digest()