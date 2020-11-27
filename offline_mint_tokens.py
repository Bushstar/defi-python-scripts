#!/usr/bin/env python3
# Copyright (c) DeFi Blockchain Developers

'''
Following script requires these Python packages to be installed with pip3
or your package management software.

base58, ecdsa, hashlib and python_bitcoinlib
'''

import json, sys
from decimal import Decimal

# defi directory must be included
from defi.transactions import changeEndianness, intToBytes, makeSignedTransaction

# Help info
if len(sys.argv) != 5:
    print('\nUsage: offline_mint_tokens.py tokenID amount "private key" "input"\n\n'
        'tokenID (number): token identifier\n\n'
        'amount (number): number of tokens to create\n\n'
        'private key (string): private key to sign transaction. Input MUST be from this key and\n'
        'be the owner of the token we are minting tokens for.\n\n'
        'intput (string): UTXO for the collateral address, amount to spend in UTXO, change sent\n'
        'to private key address, 0.0001 fee.\n'
        'intput example: \'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]\'\n'
        )
    sys.exit()

# Parse JSON from client
def ParseJSON(metaFromArg):
    try:
        return json.loads(metaFromArg)
    except ValueError:
        print("Error parsing JSON:", metaFromArg)
        sys.exit()

# Get token ID argument
try:
    tokenID = int(sys.argv[1])
except:
    print("tokenID must be an integer")
    sys.exit()

tokenID = changeEndianness(intToBytes(tokenID, 4)).decode()

# Get the amount of tokens to mint
try:
    amount = int(sys.argv[2])
except:
    print("amount must be an integer")
    sys.exit()

amount *= 100000000 # Multiply by nuber of Satoshis (COIN)
amount = changeEndianness(intToBytes(amount, 8)).decode()

# Get private key
privateKey = sys.argv[3]

# Get input
utxo = ParseJSON(sys.argv[4])

# Parsed input should be list with one element, we only accept a single UTXO in this script
# but keep the input argument the same as the updatetoken RPC call for consistency.
if len(utxo) != 1:
    print("input should be a list")
    sys.exit()

utxo = utxo[0] # Get first element in list

# Does input have correct keys?
if not "txid" in utxo or not "vout" in utxo or not "amount" in utxo:
    print("input argument missing keys")
    sys.exit()

# Are input values at least the correct type?
if not isinstance(utxo['txid'], str):
    print("input txid must be a string")
    sys.exit()
if not isinstance(utxo['vout'], int):
    print("input vout must be an integer")
    sys.exit()
if not isinstance(utxo['amount'], str):
    print("input vout must be an string")
    sys.exit()

# Check input amount
try:
    inputAmount = Decimal(utxo['amount']) - Decimal("0.0001") # Deduct 0.0001 fee
except:
    print("amount value in input arg not a number")
    sys.exit()

if inputAmount < 0:
    print("input amount too small to cover fee")
    sys.exit()

# Convert to Satoshis
inputAmount = int(100000000 * inputAmount)

# Create mint tokens payload
outputTokenPayload = "146a12446654784d01" + tokenID + amount

# Create and print signed raw transaction
print("Signed TX:", makeSignedTransaction(privateKey, utxo['txid'], utxo['vout'], inputAmount, outputTokenPayload))
