import random
import tempfile
import unittest
from pathlib import Path

import insults


class InsultGeneratorTests(unittest.TestCase):
    def test_clean_target_name_preserves_casing_and_internal_spacing(self):
        self.assertEqual(
            insults.clean_target_name("  xX  Strange Name_Xx  "),
            "xX  Strange Name_Xx",
        )

    def test_format_insult_parts_cleans_spacing_around_inserted_name(self):
        result = insults.format_insult_parts(
            ['"Dummy"', "  xX_Player_Xx  ", "is totally biased.", "Wow!"]
        )

        self.assertEqual(result, '"Dummy" xX_Player_Xx is totally biased. Wow!')

    def test_format_insult_parts_removes_space_before_punctuation(self):
        result = insults.format_insult_parts(["Hello ,", "Player", "wins !"])

        self.assertEqual(result, "Hello, Player wins!")

    def test_config_round_trip_preserves_target_and_context(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"

            insults.save_config(
                {"target": "xX_Player_Xx", "context": "ranked match", "hotkey": "F8"},
                path=config_path,
            )

            self.assertEqual(
                insults.load_config(path=config_path),
                {"target": "xX_Player_Xx", "context": "ranked match", "hotkey": "F8"},
            )

    def test_generate_and_copy_uses_target_and_clipboard_once(self):
        copied = []
        rng = random.Random(2)

        insult = insults.generate_and_copy(
            "xX_Player_Xx",
            clipboard_copy=copied.append,
            rng=rng,
        )

        self.assertEqual(copied, [insult])
        self.assertIn("xX_Player_Xx", insult)

    def test_hotkey_to_vk_accepts_function_keys(self):
        self.assertEqual(insults.hotkey_to_vk("F8"), 0x77)
        self.assertEqual(insults.hotkey_to_vk("f12"), 0x7B)

    def test_hotkey_to_vk_rejects_unsupported_keys(self):
        with self.assertRaises(ValueError):
            insults.hotkey_to_vk("ENTER")

    def test_validate_quote_data_accepts_current_corpus(self):
        errors = insults.validate_quote_data(insults.load_quotes())

        self.assertEqual(errors, [])

    def test_validate_quote_data_reports_missing_template_key(self):
        quote_data = {
            "subjectnamesecond": ["Crooked"],
            "subjectnametwice1": ["I've warned about "],
            "subjectnametwice2": ["for years."],
            "predicate": ["lost."],
            "insult3": ["Sad."],
            "kicker": ["Wow!"],
        }

        errors = insults.validate_quote_data(quote_data)

        self.assertIn("Missing quote category: subjectnamefirst", errors)

    def test_validate_quote_data_reports_blank_fragments(self):
        quote_data = {key: ["Valid"] for key in insults.required_quote_keys()}
        quote_data["kicker"] = ["  "]

        errors = insults.validate_quote_data(quote_data)

        self.assertIn("Blank quote fragment in category: kicker", errors)


if __name__ == "__main__":
    unittest.main()
