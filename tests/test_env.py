import unittest

from new8021x.env import InterfaceInfo, suggest_layout_from_interfaces


class SuggestLayoutTests(unittest.TestCase):
    def test_suggest_layout_prefers_carrier_upstream_and_second_wired_downstream(self) -> None:
        interfaces = [
            InterfaceInfo(
                name="eth0",
                mac_address="00:11:22:33:44:55",
                mtu=1500,
                operstate="up",
                carrier=1,
                is_up=True,
                is_loopback=False,
                is_physical=True,
                is_wireless=False,
                addresses=[],
            ),
            InterfaceInfo(
                name="enx1234",
                mac_address="00:11:22:33:44:66",
                mtu=1500,
                operstate="down",
                carrier=0,
                is_up=False,
                is_loopback=False,
                is_physical=True,
                is_wireless=False,
                addresses=[],
            ),
            InterfaceInfo(
                name="wlan0",
                mac_address="00:11:22:33:44:77",
                mtu=1500,
                operstate="up",
                carrier=1,
                is_up=True,
                is_loopback=False,
                is_physical=False,
                is_wireless=True,
                addresses=[],
            ),
        ]

        suggestion = suggest_layout_from_interfaces(interfaces)
        self.assertEqual(suggestion.upstream, "eth0")
        self.assertEqual(suggestion.downstream, "enx1234")
        self.assertEqual(suggestion.sidechannel, "wlan0")


if __name__ == "__main__":
    unittest.main()

