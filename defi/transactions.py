# Copyright (c) DeFi Blockchain Developers
import struct
from abc import ABCMeta, abstractmethod
from binascii import hexlify, unhexlify
from decimal import Decimal

from bitcoin.core.script import *
from ecdsa.util import sigencode_der_canonize, sigencode_der
from hashlib import sha256

import defi.addressutils

TRANSACTION_FIXED_FEE = "10000"
ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


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


def sign_input(sk, tx_digest):
    signature = sk.sign_digest_deterministic(tx_digest, sigencode=sigencode_der, hashfunc=sha256)

    der_prefix = signature[0]
    length_total = signature[1]
    der_type_int = signature[2]
    length_r = signature[3]
    R = signature[4:4+length_r]
    length_s = signature[5 + length_r]
    S = signature[5 + length_r + 1:]
    S_as_bigint = int( hexlify(S).decode('utf-8'), 16 )

    half_order = ORDER // 2
    if S_as_bigint > half_order:
        new_S_as_bigint = ORDER - S_as_bigint
        new_S = unhexlify( format(new_S_as_bigint, 'x').zfill(64) )
        length_s -= 1
        length_total -= 1
    else:
        new_S = S

    signature = struct.pack('BBBB', der_prefix, length_total, der_type_int, length_r) + R + \
                    struct.pack('BB', der_type_int, length_s) + new_S

    signature += struct.pack('B', 1)

    return hexlify(signature).decode('utf-8')


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

    @abstractmethod
    def P2WPKH(self):
        pass

    @abstractmethod
    def P2SH(self):
        pass

class InputScript(BaseScript):

    @classmethod
    def P2PKH(cls, sig, pk):
        script = cls()
        script.content = script.serialize("<" + sig.decode() + "> <" + pk + ">")

        return script

    @classmethod
    def P2WPKH(self):
        pass

    @classmethod
    def P2SH(self):
        pass


class OutputScript(BaseScript):

    @classmethod
    def P2PKH(cls, data):
        script = cls()
        script.content = script.serialize("OP_DUP OP_HASH160 <" + data + "> OP_EQUALVERIFY OP_CHECKSIG")

        return script

    @classmethod
    def P2WPKH(cls, data):
        script = cls()
        script.content = script.serialize("OP_0 <" + data + ">")

        return script

    @classmethod
    def P2SH(cls, data):
        script = cls()
        script.content = script.serialize("OP_HASH160 <" + data + "> OP_EQUAL")

        return script


def make_raw_transaction(txid, index, scriptsig, amount, payload, scriptpubkey):
    amount -= Decimal(TRANSACTION_FIXED_FEE) # Deduct 0.0001 fee
    return "0400000001" + change_endianness(txid).decode() + change_endianness(int_to_bytes(index, 4)).decode() + \
           encode_varint(len(scriptsig.content) / 2) + scriptsig.content + "ffffffff020000000000000000" + payload + \
           "00" + change_endianness(int_to_bytes(amount, 8)).decode() + encode_varint(len(scriptpubkey.content) / 2) + \
           scriptpubkey.content + "0000000000"


def make_raw_transaction_segwit(txid, index, scriptsig, amount, payload, scriptpubkey, sig, pk):
    amount -= Decimal(TRANSACTION_FIXED_FEE) # Deduct 0.0001 fee
    scriptsig = encode_varint(len(scriptsig.content) / 2) + scriptsig.content
    return "04000000000101" + change_endianness(txid).decode() + change_endianness(int_to_bytes(index, 4)).decode() + \
           encode_varint(len(scriptsig) / 2) + scriptsig + "ffffffff020000000000000000" + payload + \
           "00" + change_endianness(int_to_bytes(amount, 8)).decode() + encode_varint(len(scriptpubkey.content) / 2) + \
           scriptpubkey.content + "0002" + encode_varint(len(sig) / 2) + sig + encode_varint(len(pk) / 2) + pk + "00000000"


def make_segwit_transaction_hash(txid, index, scriptsig, amount, payload, scriptpubkey):
    # Hash prevouts
    hash_prevouts = unhexlify(txid)[::-1] + struct.pack('<L', index)
    hash_prevouts = sha256(sha256(hash_prevouts).digest()).digest()

    # Hash sequence
    hash_sequence = sha256(sha256(b'\xff\xff\xff\xff').digest()).digest() # Hard coded sequence ffffffff

    # Hash outputs
    hash_outputs = unhexlify("0000000000000000" + payload + "00") # Payload output
    script_bytes = unhexlify(scriptpubkey.content) # Change output
    output_amount = amount - Decimal(TRANSACTION_FIXED_FEE)
    hash_outputs += struct.pack('<q', int(output_amount)) + struct.pack('B', len(script_bytes)) + script_bytes + b'\x00'
    hash_outputs = sha256(sha256(hash_outputs).digest()).digest()

    # Build TX for signing
    tx_for_signing = b'\x04\x00\x00\x00' + hash_prevouts + hash_sequence + unhexlify(txid)[::-1] + struct.pack('<L', index)
    script_bytes = unhexlify(scriptsig.content)
    tx_for_signing += struct.pack('B', len(script_bytes)) + script_bytes + struct.pack('<q', amount) + b'\xff\xff\xff\xff'
    tx_for_signing += hash_outputs + b'\x00\x00\x00\x00' + struct.pack('<i', 1)

    return sha256(sha256(tx_for_signing).digest()).digest()


def make_signed_transaction(privatekey, txid, index, amount, payload, segwit=False):
    # Get various keys
    sk = defi.addressutils.signing_key(privatekey)
    vk = sk.get_verifying_key()
    pk = defi.addressutils.private_to_public_key(vk)

    pubkey_hash160 = defi.addressutils.hash160_public(pk)

    if segwit:
        redeem_script = OutputScript.P2WPKH(pubkey_hash160)
        build_p2sh_data = hexlify(defi.addressutils.hash160(redeem_script.content)).decode('utf-8')
        scriptpubkey = OutputScript.P2SH(build_p2sh_data)
        scriptsig = OutputScript.P2PKH(pubkey_hash160)

        # Generate and sign TX hash
        hash = make_segwit_transaction_hash(txid, index, scriptsig, amount, payload, scriptpubkey)
        sig = sign_input(sk, hash)

        # Generate signed TX
        signed_txn = make_raw_transaction_segwit(txid, index, redeem_script, amount, payload, scriptpubkey, sig, pk)
    else:
        scriptpubkey = OutputScript.P2PKH(pubkey_hash160)

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
