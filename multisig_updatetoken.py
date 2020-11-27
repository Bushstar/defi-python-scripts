#!/usr/bin/env python3
# Copyright (c) DeFi Blockchain Developers

import errno
import json
import os
import sys
from decimal import Decimal
from subprocess import PIPE, run


# Check for errors from running defi-cli commands
def check_error(res):
    if res.returncode == 1 or len(res.stderr) > 0:
        sys.exit(res.stderr.decode().rstrip())


# Parse JSON from client
def parse_json(meta):
    try:
        return json.loads(meta)
    except ValueError:
        sys.exit("Error parsing JSON:" + meta)


# Requires defi-cli to be present and working
if not os.path.isfile("defi-cli"):
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), "defi-cli")

# Help info
if len(sys.argv) != 6:
    sys.exit('\nUsage: multisig_updatetoken.py tokenID "metadata" "private key" "redeem script" "input"\n\n'
             'token (number): token identifier\n\n'
             'metadata (string): one or more values to change\n'
             'metadata example: \'{"name":"NAME","symbol":"SYM","isDAT":false,"mintable":true,"tradable":true,"finalize":false}\'\n\n'
             'private key (string): private key to sign transaction\n\n'
             'redeem script (string): multisig redeen script\n\n'
             'input (string): UTXO for the multisig address, amount to spend in UTXO, change sent to multisig address, 0.0001 fee\n'
             'input example: \'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]\'\n')

# Get token info from client
result = run(["./defi-cli", "gettoken", sys.argv[1]], stdout=PIPE, stderr=PIPE)
check_error(result)
tokenInfo = json.loads(result.stdout)[sys.argv[1]]

# Get metadata argument
metadata = parse_json(sys.argv[2])

# Get input
utxo = parse_json(sys.argv[5])

# Parsed input should be list with one element, we only accept a single UTXO in this script
# but keep the input argument the same as the updatetoken RPC call for consistency.
if len(utxo) != 1:
    sys.exit("input should be a list")

utxo = utxo[0]  # Get first element in list

# Does input have correct keys?
if not "txid" in utxo or not "vout" in utxo or not "amount" in utxo:
    sys.exit("input argument missing keys")

# Are input values at least the correct type?
if not isinstance(utxo['txid'], str):
    sys.exit("input txid must be a string")
if not isinstance(utxo['vout'], int):
    sys.exit("input vout must be an integer")
if not isinstance(utxo['amount'], str):
    sys.exit("input vout must be an string")

# Check input amount
try:
    inputAmount = Decimal(utxo['amount']) - Decimal("0.0001")  # Deduct 0.0001 fee
except ValueError:
    sys.exit("amount value in input arg not a number")

if inputAmount < 0:
    sys.exit("input amount too small to cover fee")

inputAmount = f"{inputAmount:.8f}"

# Get private key
privateKey = sys.argv[3]

# Get redeem script
redeemScript = sys.argv[4]

# Get multisig scriptPubkey
multisigScriptpubkey = run(["./defi-cli", "getaddressinfo", tokenInfo["collateralAddress"]], stdout=PIPE, stderr=PIPE)
check_error(multisigScriptpubkey)
multisigScriptpubkey = json.loads(multisigScriptpubkey.stdout)['scriptPubKey']

# Create payload data for OP_RETURN data output
creationTxReversed = "".join(reversed([tokenInfo['creationTx'][i:i + 2] for i in range(0, len(tokenInfo['creationTx']), 2)]))
updateTokenPayload = "446654786e" + creationTxReversed

# Add token symbol
if "symbol" in metadata:
    symbol = metadata["symbol"].strip()[0:8]  # 8 max symbol length
    updateTokenPayload += f"{len(symbol):02x}"
    updateTokenPayload += symbol.encode().hex()
else:
    updateTokenPayload += f"{len(tokenInfo['symbol']):02x}"
    updateTokenPayload += tokenInfo["symbol"].encode().hex()

# Add token name
if "name" in metadata:
    name = metadata["name"].strip()[0:128]  # 128 max symbol length
    updateTokenPayload += f"{len(name):02x}"
    updateTokenPayload += name.encode().hex()
else:
    updateTokenPayload += f"{len(tokenInfo['symbol']):02x}"
    updateTokenPayload += tokenInfo["symbol"].encode().hex()

# Add uint8_t decimal, fixed to 8 places
updateTokenPayload += "08"

# Add int64_t limit, not tracked
updateTokenPayload += "0000000000000000"

# Get bools for flags
if "mintable" in metadata:
    mintable = metadata['mintable']
else:
    mintable = tokenInfo['mintable']

if "tradable" in metadata:
    tradable = metadata['tradable']
else:
    tradable = tokenInfo['tradable']

if "isDAT" in metadata:
    isDAT = metadata['isDAT']
else:
    isDAT = tokenInfo['isDAT']

if "finalize" in metadata:
    finalize = metadata['finalize']
else:
    finalize = tokenInfo['finalized']

# Set token flags
flag = 0

if mintable:
    flag |= 0x01

if tradable:
    flag |= 0x02

if isDAT:
    flag |= 0x04

if finalize:
    flag |= 0x10

# Add flag to payload data
updateTokenPayload += f"{flag:02x}"

# Create raw transaction
rawTx = run(["./defi-cli", "createrawtransaction", '[{"txid":"' + utxo['txid'] + '","vout":' + str(utxo['vout']) + '}]',
             '[{"data":"' + updateTokenPayload + '"},{"' + tokenInfo["collateralAddress"] + '":' + inputAmount + '}]'], stdout=PIPE, stderr=PIPE)
check_error(rawTx)
rawTx = rawTx.stdout.decode().rstrip()  # Remove new line

# Create signed raw transaction
signedRawtx = run(["./defi-cli", "signrawtransactionwithkey", rawTx, '["' + privateKey + '"]', '[{"txid":"' + utxo['txid'] + '","vout":' + str(utxo['vout']) +
                   ',"scriptPubKey":"' + multisigScriptpubkey + '","redeemScript":"' + redeemScript + '"}]'], stdout=PIPE, stderr=PIPE)
check_error(signedRawtx)
signedRawtx = json.loads(signedRawtx.stdout)['hex']

# Send raw transaction
sendResult = run(["./defi-cli", "sendrawtransaction", signedRawtx], stdout=PIPE, stderr=PIPE)
check_error(sendResult)

print(sendResult.stdout.decode().rstrip())
