"""Answer comparison for execution-accuracy grading, shared by the eval scripts.

A generated query is correct when its result rows equal the gold rows as a
multiset: column names are free, row order is not graded, every row must
match one gold row value for value, extra columns fail, floats match within
a relative 1e-6, and integers and floats compare by value.

Two rules differ from the grader the NORA (v1) results were scored with,
which is kept in eval/rescore.py so those numbers stay reproducible:
- Booleans match only booleans. v1 compared with ==, and in Python
  True == 1, so RETURN true passed the 12 items whose gold is 1 (review S7;
  no model did this).
- A single row holding a single list, which is what
  RETURN collect(x) AS answer produces, is read as one row per element.
  v1 compared the list itself against the gold rows and so failed all 113
  such queries, the semantically right ones included (review S6). Elements
  that are maps or lists become multi-column rows. No gold answer contains
  a list, so the rule cannot make a gold row match differently.
"""
import math


def norm_val(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, int):
        return float(v)
    if isinstance(v, str):
        return v.strip()
    return v


def val_eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    a, b = norm_val(a), norm_val(b)
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)
    return a == b


def row_eq(gold_row, got_row):
    """Same number of values, and a perfect matching between gold and
    generated values. Column names are ignored; extra columns fail, since
    the prompt instructs models to return only what is asked."""
    gs, hs = list(gold_row.values()), list(got_row.values())
    if len(gs) != len(hs):
        return False
    remaining = list(hs)
    for v in gs:
        for i, w in enumerate(remaining):
            if val_eq(v, w):
                del remaining[i]
                break
        else:
            return False
    return True


def unpack_collected(rows):
    """One row with one list-valued column -> one row per list element."""
    if len(rows) == 1 and len(rows[0]) == 1:
        (v,) = rows[0].values()
        if isinstance(v, list):
            out = []
            for e in v:
                if isinstance(e, dict):
                    out.append(dict(e))
                elif isinstance(e, (list, tuple)):
                    out.append(dict(enumerate(e)))
                else:
                    out.append({"answer": e})
            return out
    return rows


def compare(gold_rows, got_rows):
    """Multiset comparison of rows by greedy matching."""
    got_rows = unpack_collected(got_rows)
    if len(gold_rows) != len(got_rows):
        return False
    remaining = list(got_rows)
    for g in gold_rows:
        for i, h in enumerate(remaining):
            if row_eq(g, h):
                del remaining[i]
                break
        else:
            return False
    return True
