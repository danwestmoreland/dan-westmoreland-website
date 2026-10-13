#!/usr/bin/env python3
"""Build one landing page per row of accounts.csv.

Usage: python3 build.py
Reads accounts.csv and template.html from this folder and writes
../../demo/account-pages/<slug>/index.html for each row.
Every {{column}} token in the template is replaced with that row's value,
HTML-escaped so names like "Cobblestone Freight & Co." do not break the page.
"""
import csv, html, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "demo", "account-pages")

template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
tokens = set(re.findall(r"{{(\w+)}}", template))

with open(os.path.join(HERE, "accounts.csv"), newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for row in rows:
    missing = tokens - set(row)
    if missing:
        raise SystemExit(f"{row['slug']}: CSV has no column for {sorted(missing)}")
    page = template
    for key, value in row.items():
        page = page.replace("{{" + key + "}}", html.escape(value.strip()))
    folder = os.path.join(OUT, row["slug"])
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as out:
        out.write(page)
    print("wrote /demo/account-pages/" + row["slug"] + "/")

print(f"{len(rows)} pages built")
