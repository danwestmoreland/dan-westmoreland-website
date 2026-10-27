#!/usr/bin/env python3
"""Hiring-signal workflow, the mock.

Usage: python3 match.py [YYYY-MM-DD]
Reads postings.csv (fake job postings) and icp.csv (the rules), applies
the rules in order, and prints the two first lines for every posting that
qualifies: one to the hiring manager now, one to the new hire later.
The real version runs these same rules in Clay; this is so you can read them.
"""
import csv, os, re, sys
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()

rules = {r["rule"]: r["value"] for r in csv.DictReader(open(os.path.join(HERE, "icp.csv"), encoding="utf-8"))}
signal = re.compile(rules["signal_titles"], re.I)
exclude = re.compile(rules["exclude_title_words"], re.I)
industries = set(rules["industries"].split("|"))
countries = set(rules["countries"].split("|"))
skip_crm = set(rules["skip_crm_status"].split("|"))
max_age = int(rules["max_posting_age_days"])
followup = int(rules["followup_days_after_posting"])

postings = list(csv.DictReader(open(os.path.join(HERE, "postings.csv"), encoding="utf-8")))
seen, dropped, sends = set(), {}, []

def drop(reason):
    dropped[reason] = dropped.get(reason, 0) + 1

for p in postings:
    age = (today - datetime.strptime(p["posted"], "%Y-%m-%d").date()).days
    hc = int(p["headcount"])
    if p["domain"] in seen:                           drop("duplicate company"); continue
    seen.add(p["domain"])
    if not signal.search(p["title"]):                 drop("title is not the signal"); continue
    if exclude.search(p["title"]):                    drop("junior or senior variant"); continue
    if not (int(rules["headcount_min"]) <= hc <= int(rules["headcount_max"])): drop("headcount out of band"); continue
    if p["industry"] not in industries:               drop("industry not a fit"); continue
    if p["country"] not in countries:                 drop("country not a fit"); continue
    if age > max_age:                                 drop("posting older than 30 days"); continue
    if p["crm_status"] in skip_crm:                   drop("already in the CRM"); continue
    if int(p["ops_titles_today"]) > 0:                drop("not their first ops hire"); continue
    if not p["pain_line"].strip():                    drop("posting has no pain line to quote"); continue
    sends.append(p)

print(f"# {len(postings)} postings, {len(sends)} qualified")
print("# dropped: " + ", ".join(f"{n} {why}" for why, n in sorted(dropped.items(), key=lambda kv: -kv[1])))
print()
def lc(s):
    s = s.strip().rstrip(".")
    return s[:1].lower() + s[1:]

for p in sends:
    tools = p["tools"].split(", ")
    stack = tools[0] if len(tools) == 1 else ", ".join(tools[:-1]) + " and " + tools[-1]
    when = (datetime.strptime(p["posted"], "%Y-%m-%d").date() + timedelta(days=followup)).isoformat()
    print(f"-> {p['company']}  ({p['headcount']} people, {p['industry']}, {p['country']})  posted {p['posted']}, reports to {p['reports_to']}")
    print(f"   now, to the {p['reports_to']}:")
    print(f"   \"You're hiring your first {p['title']} and the posting says {lc(p['pain_line'])}.")
    print(f"    The first 90 days of that hire usually go to {lc(p['first_duty'])}, in {stack}.\"")
    print(f"   {when}, to whoever gets the job:")
    print(f"   \"Congrats on the new role. From the posting, it looks like {lc(p['first_duty'])} is job one.\"")
    print()
