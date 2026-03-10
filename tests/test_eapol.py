import unittest

from new8021x.eapol import parse_eapol_frame


def frame_from_hex(value: str) -> bytes:
    return bytes.fromhex(value.replace(" ", ""))


class EapolParserTests(unittest.TestCase):
    def test_parse_eapol_start(self) -> None:
        frame = frame_from_hex(
            "0180c2000003 aabbccddeeff 888e 01 01 0000"
        )
        parsed = parse_eapol_frame(frame)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.src_mac, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(parsed.eapol_type_name, "start")
        self.assertIsNone(parsed.eap_type_name)

    def test_parse_response_identity(self) -> None:
        frame = frame_from_hex(
            "0180c2000003 aabbccddeeff 888e "
            "01 00 0009 "
            "02 07 0009 01 75736572"
        )
        parsed = parse_eapol_frame(frame)

        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed.eapol_type_name, "eap-packet")
        self.assertEqual(parsed.eap_code_name, "response")
        self.assertEqual(parsed.eap_type_name, "identity")
        self.assertEqual(parsed.identity, "user")


if __name__ == "__main__":
    unittest.main()

