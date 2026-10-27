#!/usr/bin/env python3
"""Closed-lost reactivation, the mock.

Usage: python3 reactivate.py [YYYY-MM-DD]
Reads deals.csv (fake closed-lost deals from the CRM) and changes.csv (what the
research step found at each account), keeps the deals in the 6-to-18-month
window, grades each change as material or not against the reason the deal was
lost, and prints the opener for the material ones. In the real build the
research is an API call and the grade is an LLM step with this same table as
its instructions; here it is a dict so you can read it.
"""
import csv, os, sys
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
WINDOW = (180, 548)          # days since close: 6 to 18 months
QUIET = 90                   # days since last touch before we may write again

# loss reason -> the kinds of change that answer it
MATERIAL = {
    "budget":        {"funding", "new_locations"},
    "timing":        {"new_locations", "new_leader"},
    "competitor":    {"new_leader", "competitor_contract_ending"},
    "champion left": {"new_person_in_role"},
    "no decision":   {"new_leader", "new_locations", "funding"},
}

# (loss reason, change type) -> the opener. {detail} is the research finding in plain words.
OPENER = {
    ("budget", "funding"):                     "When we talked in {month}, budget was the blocker. Since then you {detail}, which usually changes that conversation.",
    ("budget", "new_locations"):               "When we talked in {month}, budget was the blocker. You've since {detail}, and the scheduling problem gets more expensive with every location.",
    ("timing", "new_locations"):               "In {month} you said it wasn't the right time. You've since {detail}, which is usually when the right time shows up.",
    ("timing", "new_leader"):                  "In {month} the timing was off. I saw you {detail}, and a new ops leader tends to reopen the scheduling question in their first quarter.",
    ("competitor", "new_leader"):              "You went with another scheduling tool in {month}. I saw you {detail}; if the new leader is reviewing what's in place, I'd like to be on the list.",
    ("competitor", "competitor_contract_ending"): "You went with another scheduling tool in {month}. If that was a 12-month term it comes up soon, and I'd like to be in the comparison this time.",
    ("champion left", "new_person_in_role"):   "Your predecessor and I talked about scheduling in {month}, before they left. Nothing was decided. Worth 20 minutes to show you where it ended up?",
    ("no decision", "new_leader"):             "We talked in {month} and it never came to a decision. I saw you {detail}; happy to send the short version of what we covered so it doesn't start from zero.",
    ("no decision", "new_locations"):          "We talked in {month} and it never came to a decision. You've since {detail}, and that is usually the point where it comes back.",
    ("no decision", "funding"):                "We talked in {month} and it never came to a decision. Since then you {detail}, so I wanted to put it back in front of you.",
}

deals = list(csv.DictReader(open(os.path.join(HERE, "deals.csv"), encoding="utf-8")))
changes = {c["deal_id"]: c for c in csv.DictReader(open(os.path.join(HERE, "changes.csv"), encoding="utf-8"))}
counts, sends = {}, []

def tally(k): counts[k] = counts.get(k, 0) + 1

for d in deals:
    closed = datetime.strptime(d["closed_date"], "%Y-%m-%d").date()
    age = (today - closed).days
    quiet = (today - datetime.strptime(d["last_touch"], "%Y-%m-%d").date()).days
    if age < WINDOW[0]:                     tally("too recent"); continue
    if age > WINDOW[1]:                     tally("too old"); continue
    if quiet < QUIET:                       tally("touched in the last 90 days"); continue
    c = changes.get(d["deal_id"])
    if not c:                               tally("no change found"); continue
    if c["change_type"] not in MATERIAL[d["loss_reason"]]:
                                            tally("change not material to the loss reason"); continue
    if d["contact_still_there"] == "no" and not c["new_contact"]:
                                            tally("contact gone, no replacement found"); continue
    sends.append((d, c))

print(f"# {len(deals)} closed-lost deals, {len(sends)} get an email")
print("# skipped: " + ", ".join(f"{n} {why}" for why, n in sorted(counts.items(), key=lambda kv: -kv[1])))
print()
for d, c in sends:
    to = c["new_contact"] or d["contact"]
    month = datetime.strptime(d["closed_date"], "%Y-%m-%d").strftime("%B %Y")
    line = OPENER[(d["loss_reason"], c["change_type"])].format(month=month, detail=c["detail"])
    print(f"-> {d['company']}  lost {d['closed_date']} ({d['loss_reason']}), owner {d['owner']}, to {to}")
    print(f"   change: {c['change_type']} on {c['change_date']}  [{c['source']}]")
    print(f"   \"{line}\"")
    print()
