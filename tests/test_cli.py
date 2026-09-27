import unittest

from pitchtuna.cli import build_parser, main


class TestCli(unittest.TestCase):
    def test_defaults(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.instrument, "guitar")
        self.assertEqual(args.a4, 440.0)
        self.assertEqual(args.capo, 0)

    def test_parse_instrument(self):
        args = build_parser().parse_args(["-i", "ukulele", "--a4", "442"])
        self.assertEqual(args.instrument, "ukulele")
        self.assertEqual(args.a4, 442.0)

    def test_list_instruments(self):
        self.assertEqual(main(["--list-instruments"]), 0)

    def test_convert_note(self):
        self.assertEqual(main(["--note", "A4"]), 0)

    def test_convert_freq(self):
        self.assertEqual(main(["--freq", "440"]), 0)

    def test_smoke_test(self):
        self.assertEqual(main(["--smoke-test"]), 0)

    def test_version_exits(self):
        with self.assertRaises(SystemExit):
            main(["--version"])


if __name__ == "__main__":
    unittest.main()
