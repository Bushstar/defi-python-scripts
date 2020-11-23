#!/usr/bin/env python3
# Copyright (c) DeFi Blockchain Developers

'''
Tested with the following on regtest

1 address: mzzrvpfZePK1YCxcrjrUSN5ZjNek8CGW68
1 pubkey: cRnkms5jMXYbEgHCpVZm3P98UxDXnnhWVsyjRW8rSyZkSE24gAhC
1 privkey: 03e21490f4ef0f1eb20d08bc9caf8a574279ac742a9f3693e6e92dfb51f35a39fa

2 address: mmhR11Ge5ocqwrt9FUTTPpYtC4r54rtAak
2 pubkey:  cPRKopHk56rpaYF2TPCgNwmBxW56LzgiWRnxhPwXPMsd2MJUALjm
2 privkey: 025d35c5555443747756b233c1c4eaaddff048c5bfc9218cb1de5ce54f4b260405

createmultisig 1 '["03e21490f4ef0f1eb20d08bc9caf8a574279ac742a9f3693e6e92dfb51f35a39fa","025d35c5555443747756b233c1c4eaaddff048c5bfc9218cb1de5ce54f4b260405"]'

Result:
{
  "address": "2N9VF8YhdmJDzcpARFMAQGdSYo4ik7J5SCJ",
  "redeemScript": "512103e21490f4ef0f1eb20d08bc9caf8a574279ac742a9f3693e6e92dfb51f35a39fa21025d35c5555443747756b233c1c4eaaddff048c5bfc9218cb1de5ce54f4b26040552ae"
}

Created new token with multisig set as collateral address. Funded multisig address with 1 coin noting TXID and vout, used multisig_updatetoken.py in following format.

multisig_updatetoken.py tokenID "metadata" "private key" "redeem script" "input"

With real values it looked like the following.

./multisig_updatetoken.py 130 '{"symbol":"NOOT2","name":"Noot2"}' "cRnkms5jMXYbEgHCpVZm3P98UxDXnnhWVsyjRW8rSyZkSE24gAhC" "512103e21490f4ef0f1eb20d08bc9caf8a574279ac742a9f3693e6e92dfb51f35a39fa21025d35c5555443747756b233c1c4eaaddff048c5bfc9218cb1de5ce54f4b26040552ae" '[{"txid":"28b2c5b665787c04964df131ecda9f955dc9fbd8f7aae155f680db1e9e3d1c9e","vout":1,"amount":"1"}]'
'''

import binascii, errno, json, os, sys
from decimal import Decimal
from subprocess import PIPE, run

# Check for errors from running defi-cli commands
def CheckError(result):
    if result.returncode == 1 or len(result.stderr) > 0:
        print(result.stderr.decode().rstrip())
        sys.exit()

# Parse JSON from client
def ParseJSON(metaFromArg):
    try:
        return json.loads(metaFromArg)
    except ValueError:
        print("Error parsing JSON:", metaFromArg)
        sys.exit()

# Requires defi-cli to be present and working
if not os.path.isfile("defi-cli"):
    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), "defi-cli")

# Help info
if len(sys.argv) != 6:
    print('\nUsage: multisig_updatetoken.py tokenID "metadata" "private key" "redeem script" "input"\n\n'
        'token (number): token identifier\n\n'
        'metadata (string): one or more values to change\n'
        'metadata example: \'{"name":"NAME","symbol":"SYM","isDAT":false,"mintable":true,"tradable":true,"finalize":false}\'\n\n'
        'private key (string): private key to sign transaction\n\n'
        'redeem script (string): multisig redeen script\n\n'
        'intput (string): UTXO for the multisig address, amount to spend in UTXO, change sent to multisig address, 0.0001 fee\n'
        'intput example: \'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]\'\n'
        )
    sys.exit()

# Get token info from client
result = run(["./defi-cli","gettoken",sys.argv[1]], stdout=PIPE, stderr=PIPE)
CheckError(result)
tokenInfo = json.loads(result.stdout)[sys.argv[1]]

# Get metadata argument
metadata = ParseJSON(sys.argv[2])

# Get input
utxo = ParseJSON(sys.argv[5])

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

inputAmount = f"{inputAmount:.8f}"

# Get private key
privateKey = sys.argv[3]

# Get redeem script
redeemScript = sys.argv[4]

# Get multisig scriptPubkey
multisigScriptpubkey = run(["./defi-cli","getaddressinfo", tokenInfo["collateralAddress"]], stdout=PIPE, stderr=PIPE)
CheckError(multisigScriptpubkey)
multisigScriptpubkey = json.loads(multisigScriptpubkey.stdout)['scriptPubKey']

# Create payload data for OP_RETURN data output
creationTxReversed = "".join(reversed([tokenInfo['creationTx'][i:i+2] for i in range(0, len(tokenInfo['creationTx']), 2)]))
updateTokenPayload = "446654786e" + creationTxReversed

# Add token symbol
if "symbol" in metadata:
    symbol = metadata["symbol"].strip()[0:8] # 8 max symbol length
    updateTokenPayload += f"{len(symbol):02x}"
    updateTokenPayload += symbol.encode().hex()
else:
    updateTokenPayload += f"{len(tokenInfo['symbol']):02x}"
    updateTokenPayload += tokenInfo["symbol"].encode().hex()

# Add token name
if "name" in metadata:
    name = metadata["name"].strip()[0:128] # 128 max symbol length
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

if "tradeable" in metadata:
    tradeable = metadata['tradeable']
else:
    tradeable = tokenInfo['tradeable']

if "isDAT" in metadata:
    isDAT = metadata['isDAT']
else:
    isDAT = tokenInfo['isDAT']

if "finalize" in metadata:
    finalize =  metadata['finalize']
else:
    finalize = tokenInfo['finalized']

# Set token flags
flag = 0

if mintable:
    flag |= 0x01

if tradeable:
    flag |= 0x02

if isDAT:
    flag |= 0x04

if finalize:
    flag |= 0x10

# Add flag to payload data
updateTokenPayload += f"{flag:02x}"

# Create raw transaction
rawTx = run(["./defi-cli","createrawtransaction",'[{"txid":"' + utxo['txid'] + '","vout":' + str(utxo['vout']) + '}]',
    '[{"data":"' + updateTokenPayload + '"},{"' + tokenInfo["collateralAddress"] + '":' + inputAmount + '}]'], stdout=PIPE, stderr=PIPE)
CheckError(rawTx)
rawTx = rawTx.stdout.decode().rstrip() # Remove new line

# Create signed raw transaction
signedRawtx = run(["./defi-cli","signrawtransactionwithkey", rawTx, '["' + privateKey + '"]', '[{"txid":"' + utxo['txid'] + '","vout":' + str(utxo['vout']) +
    ',"scriptPubKey":"' + multisigScriptpubkey + '","redeemScript":"' + redeemScript + '"}]'], stdout=PIPE, stderr=PIPE)
CheckError(signedRawtx)
signedRawtx = json.loads(signedRawtx.stdout)['hex']

# Send raw transaction
sendResult = run(["./defi-cli","sendrawtransaction", signedRawtx], stdout=PIPE, stderr=PIPE)
CheckError(sendResult)

print(sendResult.stdout.decode().rstrip())
