#!/usr/bin/env python3
"""Route website visitor sessions to the right rep and print the Slack message.

Usage: python3 route.py
Reads sessions.csv and rules.csv from this folder. In production the sessions
arrive one at a time from your visitor ID tool's webhook, and the print at the
bottom becomes a POST to a Slack incoming webhook. The rules are the same.
"""
import csv, os
from collections import defaultdict
from itertools import cycle

HERE = os.path.dirname(os.path.abspath(__file__))
rules = list(csv.DictReader(open(os.path.join(HERE, "rules.csv"), encoding="utf-8")))
get = lambda t: [r for r in rules if r["type"] == t]

IGNORE = {r["value"] for r in get("ignore")}
MIN_HEADCOUNT = int(get("min_headcount")[0]["value"])
COUNTRIES = {r["value"] for r in get("country")}
INTENT = [r["value"] for r in get("intent_page")]
OWNER = {r["key"]: r["value"] for r in get("owner")}
TERRITORY = {r["key"]: r["value"] for r in get("territory")}
SDRS = cycle([r["value"] for r in get("sdr")])

def is_intent(pages):
    hits = [p for p in pages if any(p.startswith(i) for i in INTENT)]
    return "/pricing" in pages or len(hits) >= 2

def pick_rep(s):
    if OWNER.get(s["domain"]):
        return OWNER[s["domain"]], "CRM owner"
    if s["state"] in TERRITORY:
        return TERRITORY[s["state"]], f"territory: {s['state']}"
    return next(SDRS), "round robin"

sessions = list(csv.DictReader(open(os.path.join(HERE, "sessions.csv"), encoding="utf-8")))
last_sent = {}           # domain -> (day, person_title)
dropped = defaultdict(int)
messages = []

for s in sessions:
    pages = s["pages"].split("|")
    if s["domain"] in IGNORE:
        dropped["ignored domain"] += 1; continue
    if int(s["headcount"]) < MIN_HEADCOUNT or s["country"] not in COUNTRIES:
        dropped["no fit"] += 1; continue
    if not is_intent(pages):
        dropped["no intent"] += 1; continue
    prev = last_sent.get(s["domain"])
    if prev and (int(s["day"][-2:]) - int(prev[0][-2:])) < 7 and (not s["person_title"] or s["person_title"] == prev[1]):
        dropped["repeat"] += 1; continue
    rep, why = pick_rep(s)
    last_sent[s["domain"]] = (s["day"], s["person_title"])
    who = f"{s['person_title']}, person-level" if s["person_title"] else "company-level (IP match)"
    messages.append(
        f"-> {rep:8} {s['company']}  {', '.join(pages)}\n"
        f"   who: {who} | {s['industry']}, {s['headcount']} employees, {s['state']} | routed by {why}"
    )

print(f"# {len(sessions)} sessions, {len(messages)} messages")
print("# dropped: " + ", ".join(f"{v} {k}" for k, v in dropped.items()))
print()
print("\n".join(messages))
