"""Golden fixture: the Winter Arc sheet through 27 Oct 2026 (docs/05-scoring-and-awards.md).

Changing a mark here changes every expected number in test_scoring.py, so edits need review.
Rows are days 6 Oct to 27 Oct; columns are the 10 goals in template order; Y=done, N=missed, A=N/A.
"""

from datetime import date, timedelta

GOALS = [
    "Wake up 8 AM",
    "Cold shower",
    "Office before 10 AM",
    "In bed before 12 AM",
    "Cut sugar",
    "Cut oily & junk food",
    "Drink 3 L water",
    "Walk 5k steps",
    "Read 10 min",
    "Workout 30 min",
]

MARKS = """\
YNYYYYYYYY
YYYNNYYYYY
YYYYYYNYNN
YYNYYYYYNN
YYANNNNNNN
YNANNYNNNN
YYYNYYYYNY
YYYNYYYYNY
YYNNYYYYNN
YNNYYYYYYN
NNNYYYYYNN
NYANYYNYNN
NNANYYNNNN
NNNNYYYYNN
NNNNYYYYNN
YYANYYNNNN
NYNNYYYYNN
NYNNYYYYNY
YNANYYNYNN
NYANYYNYNN
YYANNYNYNN
NNNNYYNYNN""".splitlines()

START = date(2026, 10, 6)
END = date(2026, 12, 31)
LAST_LOGGED = date(2026, 10, 27)
AS_OF_TODAY = date(2026, 10, 28)  # 27 Oct is then a finished day, 28 Oct pending

_STATUS = {"Y": "yes", "N": "no", "A": "na"}


def goals() -> list[dict]:
    return [
        {"id": f"g{i}", "name": n, "active_from": START, "active_to": None}
        for i, n in enumerate(GOALS)
    ]


def entries() -> list[dict]:
    return [
        {"goal_id": f"g{i}", "entry_date": START + timedelta(days=d), "status": _STATUS[m]}
        for d, row in enumerate(MARKS)
        for i, m in enumerate(row)
    ]
