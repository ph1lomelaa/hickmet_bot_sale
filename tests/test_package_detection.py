"""Run: python -m unittest discover -s tests -p 'test_package*.py' -v."""
import unittest

from bull_project.bull_bot.core.google_sheets.client import extract_packages_from_rows
from bull_project.bull_bot.core.google_sheets.allocator import get_package_block

HEADER = ["№", "TRAIN", "VISA", "Train 15:50", "Avia", "Type of room",
          "Meal a day", "Last Name", "First Name", "Gender"]


def block(title_row, n=10, guide="Guide NIYET:"):
    rows = [title_row, ["Manager:"], [guide], HEADER]
    for i in range(1, n + 1):
        rows.append([str(i), "", "", "", "", "Double" if i % 2 else "", "HB", "", "", ""])
    rows += [[""], ["", "", "", "", "", "5"], [""], [""], [""]]
    return rows


class PackageDetectionTests(unittest.TestCase):
    def test_screenshot_layout_guide_row_is_not_a_package(self):
        rows = block(["06.01-13.01 ADDRESS"]) + block(["06.01-13.01 SWISS"])
        pkgs = extract_packages_from_rows(rows)
        self.assertEqual(list(pkgs.values()), ["06.01-13.01 ADDRESS", "06.01-13.01 SWISS"])
        self.assertEqual(list(pkgs.keys()), [1, 20])
        self.assertFalse(any("guide" in n.lower() for n in pkgs.values()))

    def test_allocator_finds_correct_block_for_each_package(self):
        rows = block(["06.01-13.01 ADDRESS"]) + block(["06.01-13.01 SWISS"])
        h1, _, _ = get_package_block(rows, "06.01-13.01 ADDRESS")
        h2, _, _ = get_package_block(rows, "06.01-13.01 SWISS")
        self.assertEqual((h1, h2), (3, 22))

    def test_keyword_names_still_work(self):
        rows = block(["16.12-23.12 NIYET/7d"]) + block(["16.12-23.12 SWISS/7d"])
        self.assertEqual(list(extract_packages_from_rows(rows).values()),
                         ["16.12-23.12 NIYET/7d", "16.12-23.12 SWISS/7d"])

    def test_date_only_in_column_a_takes_type_from_next_cell(self):
        rows = block(["06.01-13.01", "", "NIYET econom/ 7 days"])
        self.assertEqual(list(extract_packages_from_rows(rows).values()),
                         ["06.01-13.01 NIYET econom/ 7 days"])

    def test_title_with_year_and_merged_cell_offset(self):
        rows = block(["", "", "", "10.10-17.10.2026 SCAT/ALA-MED/7d"])
        self.assertEqual(list(extract_packages_from_rows(rows).values()),
                         ["10.10-17.10.2026 SCAT/ALA-MED/7d"])

    def test_fallback_without_headers_ignores_label_rows(self):
        rows = [["29.11-06.12 HIKMA/7d"], ["Guide HIKMA:"], ["Hotel Park Regis"],
                ["1", "Double", "HB", "IVANOV", "IVAN", "M"]]
        self.assertEqual(extract_packages_from_rows(rows), {1: "29.11-06.12 HIKMA/7d"})

    def test_empty_sheet(self):
        self.assertEqual(extract_packages_from_rows([]), {})


class DateSearchTests(unittest.TestCase):
    def test_january_search_does_not_match_december_sheets(self):
        import re
        from bull_project.bull_bot.core.smart_search import _date_variants
        sheets = ["06.12-13.12 SCO-JED", "06.12-13.12 NQZ-JED/SCAT",
                  "06.01-13.01 SCAT/ALA-MED", "20.12-27.12 SCO-JED"]
        found = [s for s in sheets
                 if any(re.match(rf"{re.escape(v)}(?!\d)", s) for v in _date_variants("06.01"))]
        self.assertEqual(found, ["06.01-13.01 SCAT/ALA-MED"])

    def test_past_tables_are_skipped(self):
        from datetime import datetime
        from bull_project.bull_bot.core.smart_search import _table_is_past
        now = datetime(2026, 11, 24)
        self.assertTrue(_table_is_past("JANUARY 2026", now))
        self.assertTrue(_table_is_past("JUNE-JULY-AUGUST 2026/27", now))
        self.assertFalse(_table_is_past("NOVEMBER 2026-27", now))
        self.assertFalse(_table_is_past("JANUARY 2027", now))
        self.assertFalse(_table_is_past("RAMADAN/SHAWWAL-2026", now))


if __name__ == "__main__":
    unittest.main()
