#!/usr/bin/env python3
"""The two-dollar account brief, the mock.

Usage: python3 brief.py
Reads accounts.csv (40 fake target accounts), rules.csv (the credit cap and
what each step costs), and research.csv (what each research step "found").
Runs the tiered research: a cheap yes/no question on everyone, a tech lookup
on the unknowns, the full brief only on what passes, and a hard credit cap
per account. Prints the briefs, the first lines, and the bill against
researching everyone. The real version is a Clay Workflow with a credit cap;
this is so you can read it.
"""
import csv, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
rules = {r["rule"]: r["value"] for r in csv.DictReader(open(os.path.join(HERE, "rules.csv"), encoding="utf-8"))}
CAP = float(rules["cap_credits_per_account"])
COST = {"small": float(rules["cost_stage1_small_model"]), "mid": float(rules["cost_stage1_mid_model"]),
        "tech": float(rules["cost_tech_lookup"]), "brief": float(rules["cost_stage2_brief"])}
FLAT = float(rules["cost_flat_brief_everyone"])
suites = re.compile(rules["procurement_suites"], re.I)
research = {r["domain"]: r for r in csv.DictReader(open(os.path.join(HERE, "research.csv"), encoding="utf-8"))}
accounts = list(csv.DictReader(open(os.path.join(HERE, "accounts.csv"), encoding="utf-8")))

def run(a):
    """Returns (outcome, credits, trail). Every step checks the cap before it spends."""
    r, spent, trail = research[a["domain"]], 0.0, []
    def spend(step, cost):
        nonlocal spent
        if spent + cost > CAP: return False
        spent += cost; trail.append(step); return True
    spend("stage1 " + r["s1_model"], COST[r["s1_model"]])
    answer = r["s1_answer"]
    if answer == "no":      return "dropped: has a process", spent, trail
    if answer == "unknown":
        if not spend("tech lookup", COST["tech"]): return "capped before tech lookup", spent, trail
        if suites.search(r["tech_found"]):  return f"dropped: runs {r['tech_found']}", spent, trail
    if not spend("brief", COST["brief"]):   return "capped before brief", spent, trail
    return "briefed", spent, trail

results = [(a, *run(a)) for a in accounts]
total = sum(c for _, _, c, _ in results)
briefed = [(a, c, t) for a, o, c, t in results if o == "briefed"]
capped = [(a, o, c) for a, o, c, _ in results if o.startswith("capped")]
dropped = [(a, o, c) for a, o, c, _ in results if o.startswith("dropped")]

print(f"# {len(accounts)} accounts: {len(briefed)} briefed, {len(dropped)} dropped, {len(capped)} hit the {CAP:.0f}-credit cap")
print(f"# credits used: {total:.1f}  (briefing everyone at {FLAT:.0f} each would be {FLAT * len(accounts):.0f})")
print(f"# cost per brief: {total / len(briefed):.1f} credits, against {FLAT * len(accounts) / len(briefed):.1f} the flat way")
print()
def bullets(domain): return [b.strip() for b in research[domain]["brief"].split(" | ")]
def first_line(a, b1):
    fact = re.sub(r"\s*\[https?://\S+\]\s*$", "", b1).rstrip(".")
    if not fact[1:2].isupper(): fact = fact[:1].lower() + fact[1:]
    return f"{a['buyer'].split()[0]}, one thing I noticed: {fact}. That is usually the point where someone decides to fix intake, so I wanted to be early."
for a, c, t in briefed[:3]:
    print(f"-> {a['company']}  ({a['employees']} people, {a['segment']}, {a['erp']})  {c:.1f} credits via {' > '.join(t)}")
    for b in bullets(a["domain"]): print(f"   - {b}")
    print(f"   first line to {a['buyer']}, {a['title']}:")
    print(f"   \"{first_line(a, bullets(a['domain'])[0])}\"")
    print()
print(f"... and {len(briefed) - 3} more briefs")
print()
print("# capped: the workflow stopped before the brief, logged for a human to decide")
for a, o, c in capped: print(f"   {a['company']}: {c:.1f} credits spent, {o}")
print()
print("# dropped at stage one or the tech lookup")
for a, o, c in dropped[:6]: print(f"   {a['company']}: {o}  ({c:.1f} credits)")
print(f"   ... {len(dropped) - 6} more")
