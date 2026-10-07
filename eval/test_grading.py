"""Tests for eval/grading.py.  Usage: python eval/test_grading.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grading import compare, val_eq  # noqa: E402

CASES = [
    # (description, gold, got, expected)
    ("int gold, float answer", [{"answer": 64}], [{"n": 64.0}], True),
    ("float within 1e-6", [{"answer": 1478.0}], [{"x": 1478.0004}], True),
    ("float off by 1e-4", [{"answer": 1478.0}], [{"x": 1478.2}], False),
    ("S7: true is not 1", [{"answer": 1}], [{"x": True}], False),
    ("S7: true is not 1.0", [{"answer": 1.0}], [{"x": True}], False),
    ("column names are free", [{"answer": "Bogura"}], [{"district": "Bogura"}],
     True),
    ("extra column fails", [{"answer": "Bogura"}],
     [{"d": "Bogura", "mt": 5.0}], False),
    ("row order is not graded", [{"answer": "A"}, {"answer": "B"}],
     [{"a": "B"}, {"a": "A"}], True),
    ("missing row fails", [{"answer": "A"}, {"answer": "B"}], [{"a": "A"}],
     False),
    ("S6: collect() of values", [{"answer": "A"}, {"answer": "B"}],
     [{"answer": ["B", "A"]}], True),
    ("S6: collect() of one value", [{"answer": "Hatiya"}],
     [{"answer": ["Hatiya"]}], True),
    ("S6: collect() of maps", [{"answer": "2019-20", "mt": 5.0},
                               {"answer": "2023-24", "mt": 7.0}],
     [{"rows": [{"y": "2023-24", "m": 7}, {"y": "2019-20", "m": 5}]}], True),
    ("S6: collect() of lists", [{"answer": "2019-20", "mt": 5.0}],
     [{"rows": [["2019-20", 5]]}], True),
    ("S6: collect() with a wrong element", [{"answer": "A"}, {"answer": "B"}],
     [{"answer": ["A", "C"]}], False),
    ("S6: collect() with a duplicate", [{"answer": "A"}],
     [{"answer": ["A", "A"]}], False),
    ("S6: empty collect()", [{"answer": "A"}], [{"answer": []}], False),
    ("two-column range answer", [{"answer_min": 117.0, "answer_max": 174.0}],
     [{"lo": 117, "hi": 174}], True),
    ("range in the wrong unit", [{"answer_min": 117.0, "answer_max": 174.0}],
     [{"lo": 0.117, "hi": 0.174}], False),
]


def main():
    failed = 0
    for desc, gold, got, want in CASES:
        ok = compare(gold, got) == want
        failed += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} {desc}")
    assert not val_eq(True, 1) and val_eq(True, True) and val_eq(3, 3.0)
    print(f"{len(CASES) - failed}/{len(CASES)} cases pass")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
