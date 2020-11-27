# Copyright (c) DeFi Blockchain Developers

from base58 import b58decode, b58encode
from binascii import hexlify, unhexlify
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import number_to_string
from hashlib import sha256, new

import defi.transactions


def checksum(v):
    return sha256(sha256(v).digest()).digest()[0:4]


def getBurnAddress(burnAddress):
    burnAddress = burnAddress + "X" * (34 - len(burnAddress))
    result = b58decode(burnAddress)
    checksumResult = checksum(result[:-4])

    mutableResult = bytearray(result)
    mutableResult[-4] = checksumResult[0]
    mutableResult[-3] = checksumResult[1]
    mutableResult[-2] = checksumResult[2]
    mutableResult[-1] = checksumResult[3]

    return b58encode(mutableResult).decode()


def wifToPrivateKey(s):
    b = b58decode(s)
    return hexlify(b).decode()[2:-10]


def privateKeyToPublicKey(pk):
    x_str = number_to_string(pk.pubkey.point.x(), pk.pubkey.order)
    if pk.pubkey.point.y() & 1:
        prefix = '03'
    else:
        prefix = '02'
    s_key = prefix + hexlify(x_str).decode()
    return s_key


def getP2PKHFromPriv(pk):
    h160 = hash160(pk)
    vh160 = chr(111).encode() + h160
    h = sha256(sha256(vh160).digest()).digest()
    addr = vh160 + h[0:4]
    addr = b58encode(addr)

    return addr


def getSigningKey(privateKey):
    return SigningKey.from_string(unhexlify(wifToPrivateKey(privateKey)), curve=SECP256k1)


def getScriptPubKeyFromAddr(addr):
    return defi.transactions.OutputScript.P2PKH(addr).content


def getScriptKeyFromPriv(privateKey):
    sk = getSigningKey(privateKey)
    vk = sk.get_verifying_key()
    pk = privateKeyToPublicKey(vk)

    return getScriptPubKeyFromAddr(getP2PKHFromPriv(pk))


def hash160FromAddr(addr):
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
