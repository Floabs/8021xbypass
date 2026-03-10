import tempfile
import unittest
from pathlib import Path
import struct

from new8021x.eapol import analyze_eapol_pcap


def build_classic_pcap(frame: bytes) -> bytes:
    global_header = struct.pack(
        "<IHHIIII",
        0xA1B2C3D4,
        2,
        4,
        0,
        0,
        65535,
        1,
    )
    record_header = struct.pack("<IIII", 0, 0, len(frame), len(frame))
    return global_header + record_header + frame


class PcapAnalysisTests(unittest.TestCase):
    def test_analyze_eapol_pcap(self) -> None:
        frame = bytes.fromhex("0180c2000003 aabbccddeeff 888e 01 01 0000".replace(" ", ""))
        pcap_bytes = build_classic_pcap(frame)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.pcap"
            path.write_bytes(pcap_bytes)
            summary = analyze_eapol_pcap(path)

        self.assertEqual(summary.frames_total, 1)
        self.assertEqual(summary.eapol_types["start"], 1)
        self.assertEqual(summary.source_kind, "pcap-file")


if __name__ == "__main__":
    unittest.main()

