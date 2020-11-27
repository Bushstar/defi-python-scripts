# Copyright (c) DeFi Blockchain Developers

'''
Following script requires these Python packages to be installed with pip3
or your package management software.

base58, ecdsa, hashlib and python_bitcoinlib
'''

import json
import sys
from decimal import Decimal

# defi directory must be included
from defi.transactions import *


# Parse JSON from client
def parse_json(meta):
    try:
        return json.loads(meta)
    except ValueError:
        print_and_exit("Error parsing JSON: " + meta)


# Print exit message and exit program
def print_and_exit(exit_message):
    sys.exit(exit_message)


# Get token ID argument
def user_token_id():
    try:
        token_id = int(sys.argv[1])
    except ValueError:
        print_and_exit("tokenID must be an integer")

    return change_endianness(int_to_bytes(token_id, 4)).decode()


# Get the amount of tokens
def user_amount():
    try:
        amount = int(sys.argv[2])
    except ValueError:
        print_and_exit("amount must be an integer")

    amount *= 100000000  # Multiply by nuber of Satoshis (COIN)
    return change_endianness(int_to_bytes(amount, 8)).decode()


# Get private key
def user_private_key():
    return sys.argv[3]


# Get input UTXO
def user_utxo():
    # Get input
    utxo = parse_json(sys.argv[4])

    # Parsed input should be list with one element, we only accept a single UTXO in this script
    # but keep the input argument the same as the updatetoken RPC call for consistency.
    if len(utxo) != 1:
        print_and_exit("input should be a list")

    utxo = utxo[0]  # Get first element in list

    # Does input have correct keys?
    if "txid" not in utxo or "vout" not in utxo or "amount" not in utxo:
        print_and_exit("input argument missing keys")

    # Are input values at least the correct type?
    if not isinstance(utxo['txid'], str):
        print_and_exit("input txid must be a string")
    if not isinstance(utxo['vout'], int):
        print_and_exit("input vout must be an integer")
    if not isinstance(utxo['amount'], str):
        print_and_exit("input amount must be an string")

    # Check input amount
    try:
        input_amount = Decimal(utxo['amount']) - Decimal("0.0001")  # Deduct 0.0001 fee
    except ValueError:
        print_and_exit("amount value in input arg not a number")

    if input_amount < 0:
        print_and_exit("input amount too small to cover fee")

    # Convert to Satoshis
    input_amount = int(100000000 * input_amount)

    return utxo['txid'], utxo['vout'], input_amount
