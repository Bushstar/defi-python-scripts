# Copyright (c) DeFi Blockchain Developers

from abc import ABCMeta, abstractmethod
from binascii import hexlify, unhexlify
from bitcoin.core.script import *
from ecdsa.util import sigencode_der_canonize, number_to_string
from hashlib import sha256

import defi.addressutils


def changeEndianness(x):
    if (len(x) % 2) == 1:
        x += "0"
    y = unhexlify(x)
    z = y[::-1]
    return hexlify(z)


def intToBytes(a, b):
    m = pow(2, 8 * b) - 1
    return ('%0' + str(2 * b) + 'x') % int(a)


def encodeVarint(value):
    if value < pow(2, 8) - 3:
        size = 1
        varint = intToBytes(value, size)
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
        varint = format(prefix, 'x') + changeEndianness(intToBytes(value, size))

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
        h160 = defi.addressutils.hash160FromAddr(data)
        script.content = script.serialize("OP_DUP OP_HASH160 <" + h160.decode() + "> OP_EQUALVERIFY OP_CHECKSIG")

        return script


def makeRawTransaction(outputTransactionHash, sourceIndex, scriptSig, inputAmount, outputTokenPayload, scriptpubkey):
    return "0400000001" + changeEndianness(outputTransactionHash).decode() + changeEndianness(intToBytes(sourceIndex, 4)).decode() + \
           encodeVarint(len(scriptSig.content) / 2) + scriptSig.content + "ffffffff020000000000000000" + outputTokenPayload + \
           "00" + changeEndianness(intToBytes(inputAmount, 8)).decode() + encodeVarint(len(scriptpubkey.content) / 2) + \
           scriptpubkey.content + "0000000000"


def makeSignedTransaction(privateKey, outputTransactionHash, sourceIndex, inputAmount, outputTokenPayload):
    # Get various keys
    sk = defi.addressutils.getSigningKey(privateKey)
    vk = sk.get_verifying_key()
    pk = defi.addressutils.privateKeyToPublicKey(vk)
    scriptPK = OutputScript.P2PKH(defi.addressutils.getP2PKHFromPriv(pk))

    # Generate unsigned TX
    unsigned_tx = makeRawTransaction(outputTransactionHash, sourceIndex, scriptPK, inputAmount, outputTokenPayload, scriptPK)

    # SIGHASH_ALL
    hc = intToBytes(1, 4)

    # Hash
    h = sha256(unhexlify(unsigned_tx + changeEndianness(hc).decode())).digest()

    # Sign
    s = sk.sign_deterministic(h, hashfunc=sha256, sigencode=sigencode_der_canonize)
    s = hexlify(s) + hc[-2:].encode()  # SIGHASH_ALL

    # Generate scriptsig
    scriptSig = InputScript.P2PKH(s, pk)

    # Make final TX
    signed_txn = makeRawTransaction(outputTransactionHash, sourceIndex, scriptSig, inputAmount, outputTokenPayload, scriptPK)

    return signed_txn
