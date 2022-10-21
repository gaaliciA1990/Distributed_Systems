"""
CPSC 5520, Seattle University
Author: Alicia Garcia
Version: 1.0

Using UDP for this, so socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Connection is never open, so you need to tell the program who to send the message to

Published messages: <timestamp, currency 1, currency 2, exchange rate>
    - timestamp:  64-bit integer number of microseconds that have passed since 00:00:00 UTC on 1 January 1970 (excluding
    leap seconds). Sent in big-endian network format.
    - currency names: three-character ISO codes ('USD', 'GBP', 'EUR', etc.) transmitted in 8-bit ASCII from left to
    right.
    - exchange rate: 64-bit floating point number represented in IEEE 754 binary64 little-endian format.
"""
