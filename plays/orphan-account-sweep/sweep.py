#!/usr/bin/env python3
"""The orphan-account sweep, the mock.

Usage: python3 sweep.py [YYYY-MM-DD]
Reads companies.csv (fake company records as HubSpot would hold them, with
deal, contact, and activity counts), icp.csv (the rules), and buyers.csv
(what the people lookup "found"). Finds every orphan, checks fit, picks the
buyer, writes the why-now, and prints the digest. The real version is one
HubSpot segment plus an n8n workflow; this is so you can read it.
"""
import csv, os, re, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
rules = {r["rule"]: r["value"] for r in csv.DictReader(open(os.path.join(HERE, "icp.csv"), encoding="utf-8"))}
lo, hi = int(rules["employees_min"]), int(rules["employees_max"])
too_new = int(rules["too_new_days"])
industries, countries = set(rules["industries"].split("|")), set(rules["countries"].split("|"))
buyer_ok = re.compile(rules["buyer_titles"], re.I)
buyers = {b["domain"]: b for b in csv.DictReader(open(os.path.join(HERE, "buyers.csv"), encoding="utf-8"))}
companies = list(csv.DictReader(open(os.path.join(HERE, "companies.csv"), encoding="utf-8")))

def is_orphan(c):
    return int(c["open_deals"]) == 0 and (int(c["contacts"]) == 0 or not c["last_contact_activity"])

def unfit(c):
    n = int(c["employees"])
    if not lo <= n <= hi:                 return f"{n} employees, outside {lo} to {hi}"
    if c["industry"] not in industries:   return f"{c['industry']} is not a market we sell to"
    if c["country"] not in countries:     return f"{c['country']} is outside our territory"
    return ""

def why_now(c, b):
    first = b["name"].split()[0]
    s = c["source"]
    if s == "visitor_id":
        return f"{first}, someone at {c['company']} spent time on our {c['detail']} and nobody here followed up. That's on us."
    if s == "rep_import":
        return f"{first}, a colleague of mine who has since moved on flagged {c['company']} back in March and never reached out. I'd rather fix that than pretend it didn't happen."
    if s == "conference_import":
        return f"{first}, {c['company']} was on our list from {c['detail']} and we never wrote. A year late is better than never."
    if s == "webinar":
        return f"{first}, somebody from {c['company']} sat in on our session \"{c['detail']}\" and we let it drop."
    ind = c["industry"].lower()
    return f"{first}, no clever reason for this one. {c['company']} is {'an' if ind[0] in 'aeiou' else 'a'} {ind} company of {c['employees']} people, which is exactly who we built this for."

orphans = [c for c in companies if is_orphan(c)]
archived, no_buyer, sequenced, new = [], [], [], []
for c in orphans:
    if (today - date.fromisoformat(c["created"])).days < too_new: new.append(c); continue
    reason = unfit(c)
    if reason:                                  archived.append((c, reason)); continue
    b = buyers.get(c["domain"])
    if not b or not buyer_ok.search(b["title"]): no_buyer.append(c); continue
    sequenced.append((c, b))

worked = len(companies) - len(orphans)
print(f"# {len(companies)} companies in the CRM, {worked} being worked, {len(orphans)} orphans")
print(f"# of the orphans: {len(sequenced)} sequenced, {len(archived)} archived, {len(new)} too new to call, {len(no_buyer)} no buyer found yet")
by_source = {}
for c in orphans: by_source[c["source"]] = by_source.get(c["source"], 0) + 1
print("# where the orphans came from: " + ", ".join(f"{n} {s.replace('_', ' ')}" for s, n in sorted(by_source.items(), key=lambda kv: -kv[1])))
print()
for c, b in sequenced:
    print(f"-> {c['company']}  ({c['employees']} people, {c['industry']}, {c['country']})  source: {c['source'].replace('_', ' ')}  to {b['name']}, {b['title']}")
    print(f"   \"{why_now(c, b)}\"")
print()
print("# archived (left the pipeline view, kept in the CRM)")
for c, reason in archived:
    print(f"   {c['company']}: {reason}")
print()
print("# no buyer found yet, retried next week")
for c in no_buyer:
    print(f"   {c['company']}")
print()
print(f"# created in the last {too_new} days, somebody may still be on it")
for c in new:
    print(f"   {c['company']}  (created {c['created']}, source: {c['source'].replace('_', ' ')})")
