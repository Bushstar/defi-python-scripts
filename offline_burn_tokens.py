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
from defi.addressutils import *
from defi.interface import *
from defi.transactions import makeSignedTransaction

# Help info
if len(sys.argv) != 5:
    print('\nUsage: offline_burn_tokens.py tokenID amount "private key" "input"\n\n'
        'tokenID (number): token identifier\n\n'
        'amount (number): number of tokens to burn\n\n'
        'private key (string): private key to sign transaction. input MUST be from this key and\n'
        'be the owner of tokens to burn.\n\n'
        'intput (string): UTXO for the token owner address, amount to spend in UTXO, change sent\n'
        'to private key address, 0.0001 fee.\n'
        'intput example: \'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]\'\n'
        )
    sys.exit()

# Get args from user
tokenID = getUserTokenID()
amount = getUserAmount()
privateKey = getUserPrivKey()
txid, vout, inputAmount = getUserUTXO()

# Get burn address
burnAddress = getBurnAddress("8addressToBurn")

# Create burn tokens payload
outputTokenPayload = "496a47446654784219" + getScriptKeyFromPriv(privateKey) + "0119" + \
                     getScriptPubKeyFromAddr(burnAddress) + "01" + tokenID + amount

# Create and print signed raw transaction
print("Signed TX:", makeSignedTransaction(privateKey, txid, vout, inputAmount, outputTokenPayload))
