# Copyright (c) DeFi Blockchain Developers

'''
Following script requires these Python packages to be installed with pip3
or your package management software.

base58, ecdsa, hashlib and python_bitcoinlib
'''

import json, sys
from decimal import Decimal

# defi directory must be included
from defi.transactions import *


# Parse JSON from client
def ParseJSON(metaFromArg):
    try:
        return json.loads(metaFromArg)
    except ValueError:
        exit("Error parsing JSON:", metaFromArg)


# Print exit message and exit program
def exit(exit_message):
    sys.exit(exit_message)


# Get token ID argument
def getUserTokenID():
    try:
        tokenID = int(sys.argv[1])
    except:
        exit("tokenID must be an integer")

    return changeEndianness(intToBytes(tokenID, 4)).decode()


# Get the amount of tokens
def getUserAmount():
    try:
        amount = int(sys.argv[2])
    except:
        exit("amount must be an integer")

    amount *= 100000000  # Multiply by nuber of Satoshis (COIN)
    return changeEndianness(intToBytes(amount, 8)).decode()


# Get private key
def getUserPrivKey():
    return sys.argv[3]


# Get input UTXO
def getUserUTXO():
    # Get input
    utxo = ParseJSON(sys.argv[4])

    # Parsed input should be list with one element, we only accept a single UTXO in this script
    # but keep the input argument the same as the updatetoken RPC call for consistency.
    if len(utxo) != 1:
        exit("input should be a list")

    utxo = utxo[0]  # Get first element in list

    # Does input have correct keys?
    if not "txid" in utxo or not "vout" in utxo or not "amount" in utxo:
        exit("input argument missing keys")

    # Are input values at least the correct type?
    if not isinstance(utxo['txid'], str):
        exit("input txid must be a string")
    if not isinstance(utxo['vout'], int):
        exit("input vout must be an integer")
    if not isinstance(utxo['amount'], str):
        exit("input amount must be an string")

    # Check input amount
    try:
        inputAmount = Decimal(utxo['amount']) - Decimal("0.0001")  # Deduct 0.0001 fee
    except:
        exit("amount value in input arg not a number")

    if inputAmount < 0:
        exit("input amount too small to cover fee")

    # Convert to Satoshis
    inputAmount = int(100000000 * inputAmount)

    return utxo['txid'], utxo['vout'], inputAmount
