import tempfile
import unittest
from pathlib import Path

from new8021x.config import load_config, write_example_config


class ConfigTests(unittest.TestCase):
    def test_load_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(
                """profile_name = "demo"

[interfaces]
upstream = "eth0"
downstream = "eth1"

[observe]
default_iface = "eth0"
duration_seconds = 30
""",
                encoding="utf-8",
            )
            config = load_config(path)

        self.assertEqual(config.profile_name, "demo")
        self.assertEqual(config.interfaces.upstream, "eth0")
        self.assertEqual(config.interfaces.downstream, "eth1")
        self.assertEqual(config.observe.default_iface, "eth0")
        self.assertEqual(config.observe.duration_seconds, 30)

    def test_write_example_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "example.toml"
            written = write_example_config(path)
            self.assertEqual(written, path)
            self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()

