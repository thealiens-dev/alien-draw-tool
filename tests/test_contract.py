import hashlib
import runpy
import unittest
from pathlib import Path

DRAW = runpy.run_path(str(Path(__file__).resolve().parents[1] / "draw.py"))


class ContractTests(unittest.TestCase):
    def test_utf16_order_matches_web_commitment(self):
        rows = sorted([(name, 1) for name in ["\ue000", "\U00010000", "a"]], key=lambda row: DRAW["canonical_username_key"](row[0]))
        self.assertEqual([name for name, _ in rows], ["a", "\U00010000", "\ue000"])
        self.assertEqual(hashlib.sha256(DRAW["build_canonical_csv_bytes"](rows)).hexdigest(), "20aa3083ede7db48d8e937dfc2ee5333ed1ef35877fae384a40867a4de79d6d8")

    def test_javascript_trim_and_header_position(self):
        parsed = DRAW["parse_participants"]("username\n\ufeffalpha\ufeff\nusername\n\u0085beta\u0085", "equal")
        self.assertEqual(parsed, {"alpha": 1, "username": 1, "\u0085beta\u0085": 1})

    def test_weighted_plain_rows_and_safe_decimal_counts(self):
        self.assertEqual(DRAW["parse_participants"]("beta,+2\r\nalpha,1", "weighted"), {"beta": 2, "alpha": 1})
        for value in ["1e2", "1.0", "0", "-1", "9007199254740992"]:
            with self.assertRaises(ValueError):
                DRAW["parse_participants"](f"alpha,{value}\nbeta,1", "weighted")

    def test_duplicates_and_output_delimiters_are_rejected(self):
        for text in ["alpha\nalpha", "alpha|beta\ngamma", "alpha,beta\ngamma"]:
            with self.assertRaises(ValueError):
                DRAW["parse_participants"](text, "equal")


if __name__ == "__main__":
    unittest.main()
