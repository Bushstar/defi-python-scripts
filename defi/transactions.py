# Copyright (c) DeFi Blockchain Developers

from abc import ABCMeta, abstractmethod
from binascii import hexlify, unhexlify
from bitcoin.core.script import *
from ecdsa.util import sigencode_der_canonize, number_to_string
from hashlib import sha256

import defi.addressutils


def change_endianness(x):
    if (len(x) % 2) == 1:
        x += "0"
    y = unhexlify(x)
    z = y[::-1]
    return hexlify(z)


def int_to_bytes(a, b):
    m = pow(2, 8 * b) - 1
    return ('%0' + str(2 * b) + 'x') % int(a)


def encode_varint(value):
    if value < pow(2, 8) - 3:
        size = 1
        varint = int_to_bytes(value, size)
    else:
        if value < pow(2, 16):
            size = 2
            prefix = 253  # 0xFD
        elif value < pow(2, 32):
            size = 4
            prefix = 254  # 0xFE
        elif value < pow(2, 64):
            size = 8
            prefix = 255  # 0xFF
        else:
            raise Exception("Wrong input data size")
        varint = format(prefix, 'x') + change_endianness(int_to_bytes(value, size)).decode()

    return varint


class BaseScript:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.content = ""

    @staticmethod
    def serialize(data):
        hex_string = ""
        for e in data.split(" "):
            if e[0] == "<" and e[-1] == ">":
                hex_string += hexlify(CScriptOp.encode_op_pushdata(unhexlify(e[1:-1]))).decode()
            elif eval(e) in OPCODE_NAMES:
                hex_string += format(eval(e), '02x')
            else:
                raise Exception

        return hex_string

    @abstractmethod
    def P2PKH(self):
        pass


class InputScript(BaseScript):

    @classmethod
    def P2PKH(cls, sig, pk):
        script = cls()
        script.content = script.serialize("<" + sig.decode() + "> <" + pk + ">")

        return script


class OutputScript(BaseScript):

    @classmethod
    def P2PKH(cls, data):
        script = cls()
        script.content = script.serialize("OP_DUP OP_HASH160 <" + data + "> OP_EQUALVERIFY OP_CHECKSIG")

        return script


def make_raw_transaction(txid, index, scriptsig, amount, payload, scriptpubkey):
    return "0400000001" + change_endianness(txid).decode() + change_endianness(int_to_bytes(index, 4)).decode() + \
           encode_varint(len(scriptsig.content) / 2) + scriptsig.content + "ffffffff020000000000000000" + payload + \
           "00" + change_endianness(int_to_bytes(amount, 8)).decode() + encode_varint(len(scriptpubkey.content) / 2) + \
           scriptpubkey.content + "0000000000"


def make_signed_transaction(privatekey, txid, index, amount, payload):
    # Get various keys
    sk = defi.addressutils.signing_key(privatekey)
    vk = sk.get_verifying_key()
    pk = defi.addressutils.private_to_public_key(vk)

    pubkey_hash160 = defi.addressutils.hash160_public(pk)

    scriptpubkey = OutputScript.P2PKH(pubkey_hash160)
    scriptsig = scriptpubkey

    # Generate unsigned TX
    unsigned_tx = make_raw_transaction(txid, index, scriptpubkey, amount, payload, scriptpubkey)

    # SIGHASH_ALL
    hc = int_to_bytes(1, 4)

    # Hash
    h = sha256(unhexlify(unsigned_tx + change_endianness(hc).decode())).digest()

    # Sign
    s = sk.sign_deterministic(h, hashfunc=sha256, sigencode=sigencode_der_canonize)
    s = hexlify(s) + hc[-2:].encode()  # SIGHASH_ALL

    # Generate scriptsig
    scriptsig = InputScript.P2PKH(s, pk)

    # Make final TX
    signed_txn = make_raw_transaction(txid, index, scriptsig, amount, payload, scriptpubkey)

    return signed_txn
