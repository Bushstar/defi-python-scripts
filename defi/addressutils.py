# Copyright (c) DeFi Blockchain Developers

from base58 import b58decode, b58encode
from binascii import hexlify, unhexlify
from ecdsa import SigningKey, SECP256k1
from ecdsa.util import number_to_string
from hashlib import sha256, new

import defi.transactions

__unusedChars = '0OIl'


def check_start_range(fst2):
    if '8F' <= fst2 <= '8d':
        return True

    return False


def get_burn_address(burn_address):
    if not burn_address:
        burn_address = "8addressToBurn"

    if len(burn_address) < 2:
        exit("Burn address too short")

    if len(burn_address) > 28:
        exit('Burn address to long, 28 chars max')

    if not burn_address.isalnum():
        exit('Burn address start string contains invalid characters')

    if any((c in burn_address) for c in __unusedChars):
        exit('Burn address start string cannot contain 0, O, I or l')

    fst2 = burn_address[0:2]
    if not check_start_range(fst2):
        exit('Address start is not correct\n'
             'Address start with string from 8F ~ 8d')

    burn_address = burn_address + "X" * (34 - len(burn_address))
    result = b58decode(burn_address)
    checksum_result = checksum(result[:-4])

    mutable_result = bytearray(result)
    mutable_result[-4] = checksum_result[0]
    mutable_result[-3] = checksum_result[1]
    mutable_result[-2] = checksum_result[2]
    mutable_result[-1] = checksum_result[3]

    return b58encode(mutable_result).decode()


def checksum(v):
    return sha256(sha256(v).digest()).digest()[0:4]


def wif_to_private_key(s):
    b = b58decode(s)
    return hexlify(b).decode()[2:-10]


def private_to_public_key(pk):
    x_str = number_to_string(pk.pubkey.point.x(), pk.pubkey.order)
    if pk.pubkey.point.y() & 1:
        prefix = '03'
    else:
        prefix = '02'
    s_key = prefix + hexlify(x_str).decode()
    return s_key


def p2pkh_from_private(pk):
    h160 = hash160(pk)
    vh160 = chr(111).encode() + h160
    h = sha256(sha256(vh160).digest()).digest()
    addr = vh160 + h[0:4]
    addr = b58encode(addr)

    return addr


def signing_key(privateKey):
    return SigningKey.from_string(unhexlify(wif_to_private_key(privateKey)), curve=SECP256k1)


def scriptpubkey_from_address(addr):
    return defi.transactions.OutputScript.P2PKH(addr).content


def getScriptKeyFromPriv(privateKey):
    sk = signing_key(privateKey)
    vk = sk.get_verifying_key()
    pk = private_to_public_key(vk)

    return scriptpubkey_from_address(p2pkh_from_private(pk))


def hash160_from_address(addr):
    decoded_addr = b58decode(addr)
    decoded_addr_hex = hexlify(decoded_addr)
    h160 = decoded_addr_hex[2:-8]

    return h160


def hash160(data):
    md = new('ripemd160')
    h = sha256(unhexlify(data)).digest()
    md.update(h)
    h160 = md.digest()

    return h160
