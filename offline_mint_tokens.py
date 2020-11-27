#!/usr/bin/env python3
# Copyright (c) DeFi Blockchain Developers

'''
Following script requires these Python packages to be installed with pip3
or your package management software.

base58, ecdsa, hashlib and python_bitcoinlib
'''

# defi directory must be included
from defi.interface import *
from defi.transactions import make_signed_transaction

# Help info
if len(sys.argv) != 5:
    print_and_exit('\nUsage: offline_mint_tokens.py tokenID amount "private key" "input"\n\n'
         'tokenID (number): token identifier\n\n'
         'amount (number): number of tokens to create\n\n'
         'private key (string): private key to sign transaction. Input MUST be from this key and\n'
         'be the owner of the token we are minting tokens for.\n\n'
         'input (string): UTXO for the collateral address, amount to spend in UTXO, change sent\n'
         'to private key address, 0.0001 fee.\n'
         'input example: \'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]\'\n')

# Get args from user
tokenID = user_token_id()
amount = user_amount()
privateKey = user_private_key()
txid, vout, inputAmount = user_utxo()

# Create mint tokens payload
outputTokenPayload = "146a12446654784d01" + tokenID + amount

# Create and print signed raw transaction
print("Signed TX:", make_signed_transaction(privateKey, txid, vout, inputAmount, outputTokenPayload))
