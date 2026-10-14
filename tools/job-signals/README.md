# Job-posting signal scanner

Finds companies on the target list that are hiring marketing leaders, SDRs, or ops roles, by reading their public Greenhouse, Lever, or Ashby job boards. No API keys.

- `companies.csv`: the seed list (domain, company, ats, slug). Leave ats/slug blank and the script discovers them; it writes them back once found.
- `signals.py`: run `python3 signals.py`. Writes `signals.csv` and prints a summary. `--discover` only finds boards.
- `seen.json`: first-seen dates per role so the weekly run can flag NEW ones. Delete it to reset.
- Signals and lanes: marketing_leader -> lane 2 (retainer); sdr, ops, sales_leader -> lane 1 (projects).

Replace the seed list with the Clay export (one row per company, domain + name) when it lands. Companies off the three ATS platforms will show as "no board found"; cover those with a job-search API later.

This folder is blocked from the public site by netlify.toml.
