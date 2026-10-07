"""Correct AWS SigV4 signing time when the local clock is off.

AWS rejects requests whose timestamp differs from server time by more than
5 minutes. This module measures the offset from the HTTP Date header of an
AWS endpoint and makes botocore sign with the corrected time. Import it
before creating any boto3 client. It is a workaround; the real fix is to
sync the operating-system clock.
"""
import datetime as _dt
import email.utils
import urllib.request

import botocore.auth

OFFSET = _dt.timedelta(0)


def measure():
    """Server time from the Date header; an HTTP error status still
    carries a valid Date header, so use it too."""
    global OFFSET
    import urllib.error
    headers = None
    try:
        req = urllib.request.Request("https://sts.amazonaws.com", method="HEAD")
        with urllib.request.urlopen(req, timeout=10) as r:
            headers = r.headers
    except urllib.error.HTTPError as e:
        headers = e.headers
    except Exception:
        headers = None
    try:
        server = email.utils.parsedate_to_datetime(headers["Date"])
        local = _dt.datetime.now(_dt.timezone.utc)
        OFFSET = server - local
    except Exception:
        OFFSET = _dt.timedelta(0)
    return OFFSET


class _Datetime(_dt.datetime):
    @classmethod
    def utcnow(cls):
        return _dt.datetime.utcnow() + OFFSET

    @classmethod
    def now(cls, tz=None):
        return _dt.datetime.now(tz) + OFFSET


class _Shim:
    datetime = _Datetime
    timezone = _dt.timezone
    timedelta = _dt.timedelta
    date = _dt.date


def _corrected_now():
    return _dt.datetime.now(_dt.timezone.utc) + OFFSET


def install():
    off = measure()
    if abs(off.total_seconds()) > 120:
        # botocore >= 1.35 signs with botocore.utils.get_current_datetime,
        # imported by name into botocore.auth; older versions used the
        # datetime module directly. Patch all three.
        import botocore.utils
        botocore.utils.get_current_datetime = _corrected_now
        if hasattr(botocore.auth, "get_current_datetime"):
            botocore.auth.get_current_datetime = _corrected_now
        botocore.auth.datetime = _Shim
        print(f"[clockskew] local clock off by {off.total_seconds()/60:.1f} min; "
              "signing with corrected time")
    return off


install()
