import struct
import unittest

from adventure_studio.scumm_binary import parse_chunks, verify_room_binary


def chunk(tag, payload):
    return tag.encode("ascii") + struct.pack(">I", len(payload) + 8) + payload


def example(*, zplane=True):
    # One 8-pixel image strip, with its LE SMAP offset from the chunk header.
    smap = chunk("SMAP", struct.pack("<I", 12) + b"\x01\x02")
    mask = chunk("ZP01", struct.pack("<H", 10) + b"\x01") if zplane else b""
    frame = chunk("IM00", smap + mask)
    room = chunk("ROOM", chunk("RMHD", struct.pack("<HHH", 8, 8, 0)) +
                 chunk("RMIM", chunk("RMIH", b"\x01\x00") + frame) +
                 chunk("OBIM", chunk("IMHD", struct.pack("<8H", 15, 0, 0, 0, 0, 0, 8, 8))) +
                 chunk("OBCD", chunk("CDHD", struct.pack("<H", 15))))
    return chunk("LECF", chunk("LFLF", room))


class BinaryStructureTests(unittest.TestCase):
    def test_linked_room_and_optional_zplane(self):
        tree = verify_room_binary(example())
        self.assertEqual(tree[0].tag, "LECF")
        self.assertEqual(tree[0].children[0].children[0].find("RMIM")[0].tag, "RMIM")
        self.assertTrue(verify_room_binary(example(zplane=False)))

    def test_xor_linked_room(self):
        data = example()
        self.assertEqual(verify_room_binary(bytes(value ^ 0x69 for value in data), xor_key=0x69),
                         verify_room_binary(data))

    def test_truncation_and_size_rejected(self):
        with self.assertRaises(ValueError):
            parse_chunks(example()[:-1])
        damaged = bytearray(example())
        damaged[4:8] = b"\x00\x00\x00\x07"
        with self.assertRaises(ValueError):
            parse_chunks(bytes(damaged))

    def test_smap_offsets_checked(self):
        damaged = example().replace(struct.pack("<I", 12), struct.pack("<I", 5000), 1)
        with self.assertRaisesRegex(ValueError, "SMAP strip"):
            verify_room_binary(damaged)

    def test_zplane_offsets_checked(self):
        damaged = example().replace(struct.pack("<H", 10) + b"\x01", b"\xff\xff\x01", 1)
        with self.assertRaisesRegex(ValueError, "ZP01 strip"):
            verify_room_binary(damaged)

    def test_unpaired_object_ids_rejected(self):
        damaged = example().replace(chunk("CDHD", struct.pack("<H", 15)),
                                    chunk("CDHD", struct.pack("<H", 16)))
        with self.assertRaisesRegex(ValueError, "OBIM/OBCD"):
            verify_room_binary(damaged)
