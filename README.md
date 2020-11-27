# DeFiChain Python Scripts
Collection of DeFiChain related scripts. Note that Python 3 required. Any problems, questions or bug reports please create a [GitHub Issue](https://github.com/Bushstar/defi-python-scripts/issues).
### [multisig_updatetoken.py](https://github.com/Bushstar/defi-python-scripts/blob/master/multisig_updatetoken.py "multisig_updatetoken.py")
Script to assist with the creation of update token transaction for tokens that are owned by 1-of-N P2SH multisig addresses. These transactions cannot easily be created using the updatetoken RPC call due to the requirement of a redeem script to spend from a multisig. Creates a raw transaction for token with multisig owner to update a token's various owner configurable values like name and symbol, there are also mintable, tradable, isDAT and finalize flags.

Place script in a directory with the defi-cli binary which should be configured to work with a running defid. defi-cli will be used to run createrawtransaction, signrawtransactionwithkey and sendrawtransaction.

Usage instructions can be viewed by running the script without any arguments.

`python3 multisig_updatetoken.py`

The following arguments are required:

**token** (number)
Token identifier.

**metadata** (string)
One or more of the token details to be updated, for example.
`'{"name":"NAME","symbol":"SYM","isDAT":false,"mintable":true,"tradable":true,"finalize":false}'`

**private key** (string)
Private key that corresponds to one of the public keys in the multisig, used to sign the raw transaction to authorize spending from the mutltisig.

**redeem script** (string)
Multisig redeem script, created when the multisig address was made, is the unlocking script required to spend funds in a multisig address.

**input** (string)
Must be a UTXO that belongs to the token owner with at least 0.0001 DFI for the fee. Requires the following information in the form shown below. txid is the transaction hash related to the UTXO, vout is the output index of the UTXO and exact amount in the UTXO.

Be careful specifying the amount, the fee will be deducted and the rest sent back to the owner address, any difference between the to will end up as the miner fee. Set the amount to 1 DFI for a 10 DFI UTXO and the miner will get 9.0001 DFI.

`'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]'`

### [offline_mint_tokens.py](https://github.com/Bushstar/defi-python-scripts/blob/master/offline_mint_tokens.py)

Offline script to create signed raw mint token transaction. Assists with managing tokens created with cold storage / offline addresses. The resulting transaction raw transaction printed by this script can be broadcast using the RPC call sendrawtransaction.

Usage instructions can be viewed by running the script without any arguments.

`python3 offline_mint_tokens.py`

The following arguments are required:

**token** (number)
Token identifier.

**amount** (number)
Amount of tokens to create.

**private key** (string)
Private key to sign the transaction, must belong to the token owner.

**input** (string)
Must be a UTXO that belongs to the token owner with at least 0.0001 DFI for the fee. Requires the following information in the form shown below. txid is the transaction hash related to the UTXO, vout is the output index of the UTXO and exact amount in the UTXO.

Be careful specifying the amount, the fee will be deducted and the rest sent back to the owner address, any difference between the to will end up as the miner fee. Set the amount to 1 DFI for a 10 DFI UTXO and the miner will get 9.0001 DFI.

`'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]'`

### [offline_burn_tokens.py](https://github.com/Bushstar/defi-python-scripts/blob/master/offline_burn_tokens.py)

Offline script to create signed raw burn token transaction. Assists with managing tokens created with cold storage / offline addresses. The resulting transaction raw transaction printed by this script can be broadcast using the RPC call sendrawtransaction.

Usage instructions can be viewed by running the script without any arguments.

`python3 offline_burn_tokens.py`

The following arguments are required:

**token** (number)
Token identifier.

**amount** (number)
Amount of tokens to create.

**private key** (string)
Private key to sign the transaction, must belong to the token owner.

**input** (string)
Must be a UTXO that belongs to the token owner with at least 0.0001 DFI for the fee. Requires the following information in the form shown below. txid is the transaction hash related to the UTXO, vout is the output index of the UTXO and exact amount in the UTXO.

Be careful specifying the amount, the fee will be deducted and the rest sent back to the owner address, any difference between the to will end up as the miner fee. Set the amount to 1 DFI for a 10 DFI UTXO and the miner will get 9.0001 DFI.

`'[{"txid":"TXID","vout":0,"amount":"0.00000000"}]'`

**burn address** (string)
Specify the start of the generated burn address, must begin with 8F to 8d and not include `0`, `O`, `I` or `l`. If no address provided then "8addressToBurn" will be used. Generated burn address is displayed as a result of running this script.
