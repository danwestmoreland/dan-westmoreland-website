#!/usr/bin/env python3
"""The ad-lead ICP loop, the mock.

Usage: python3 loop.py
Reads leads.csv (a week of fake LinkedIn lead-gen form fills as HubSpot
would hold them), icp.csv (the rules), and campaigns.csv (what each campaign
spent). Scores every lead 0 to 3, routes it, and prints the weekly campaign
report with the pause flags. The real version runs these same rules in n8n
on a five-minute poll; this is so you can read them.
"""
import csv, os, re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
rules = {r["rule"]: r["value"] for r in csv.DictReader(open(os.path.join(HERE, "icp.csv"), encoding="utf-8"))}
buyer = re.compile(rules["buyer_titles"], re.I)
exclude = re.compile(rules["exclude_title_words"], re.I)
industries = set(rules["industries"].split("|"))
countries = set(rules["countries"].split("|"))
lo, hi = int(rules["employees_min"]), int(rules["employees_max"])
pause_below = float(rules["pause_below_fit_rate"])
campaigns = list(csv.DictReader(open(os.path.join(HERE, "campaigns.csv"), encoding="utf-8")))
spend = {c["campaign"]: float(c["week_spend_usd"]) for c in campaigns}
offer = {c["campaign"]: c["offer"] for c in campaigns}
leads = list(csv.DictReader(open(os.path.join(HERE, "leads.csv"), encoding="utf-8")))

def score(l):
    s, why = 0, []
    if buyer.search(l["title"]) and not exclude.search(l["title"]): s += 1; why.append("title")
    if lo <= int(l["employees"]) <= hi:                              s += 1; why.append("size")
    if l["industry"] in industries and l["country"] in countries:   s += 1; why.append("market")
    return s, why

ROUTE = {3: "book", 2: "nurture", 1: "nurture", 0: "stop"}
by_campaign = defaultdict(lambda: {"leads": 0, "fit": 0, "nurture": 0, "stop": 0})
routed = []
for l in leads:
    s, why = score(l)
    r = ROUTE[s]
    c = by_campaign[l["campaign"]]
    c["leads"] += 1
    c["fit" if r == "book" else r] += 1
    routed.append((l, s, why, r))

n = len(leads)
books = sum(1 for _, _, _, r in routed if r == "book")
print(f"# {n} ad leads this week, {books} booked-path, "
      f"{sum(1 for *_, r in routed if r == 'nurture')} nurture, {sum(1 for *_, r in routed if r == 'stop')} stopped")
print()
for l, s, why, r in routed:
    if r != "book": continue
    print(f"-> {l['first_name']}, {l['title']} at {l['company']}  ({l['employees']} people, {l['industry']}, {l['country']})  "
          f"via {l['campaign']}  score 3  reply within {rules['reply_within_minutes']} min")
    print(f"   \"You just downloaded {offer[l['campaign']]}. If month-end expense review lands on your desk,")
    print(f"    I can show you how a {l['industry'].lower()} team of {l['employees']} gets it down to an afternoon. "
          f"Pick a time: {rules['booking_link']}\"")
print()
print("# a few that did not get the fast reply")
for l, s, why, r in routed:
    if r == "book": continue
    if l["first_name"] in ("Jules", "Nora", "Hiro", "Isla", "Amara"):
        print(f"   {l['first_name']}, {l['title']} at {l['company']}  via {l['campaign']}  score {s} ({', '.join(why) or 'nothing'})  -> {r}")
print()
print("# weekly campaign report")
print(f"{'campaign':<22}{'leads':>6}{'fit':>5}{'fit rate':>10}{'spend':>8}{'$/fit lead':>12}  action")
for name, c in sorted(by_campaign.items(), key=lambda kv: -kv[1]['fit'] / max(kv[1]['leads'], 1)):
    rate = c["fit"] / c["leads"] if c["leads"] else 0
    cpf = spend[name] / c["fit"] if c["fit"] else float("inf")
    action = "PAUSE" if rate < pause_below else "keep"
    cpf_s = f"${cpf:,.0f}" if c["fit"] else "n/a"
    print(f"{name:<22}{c['leads']:>6}{c['fit']:>5}{rate:>10.0%}{'$' + format(spend[name], ',.0f'):>8}{cpf_s:>12}  {action}")
