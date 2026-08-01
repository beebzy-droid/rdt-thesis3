"""scripts/extract_parameters.py — derive plant parameters from public statistics.

Reproduces every number in thesis/parameter_verification.md from the source files:
  ERC 2015-2023 Reliability Indices Summary (xlsx)   -> freq_D4
  PSA OpenSTAT crop production by region/quarter     -> buy_cap_frac_phi
  PSA OpenSTAT farmgate prices by region/month       -> w_nut

Run with --data DIR pointing at the directory holding those files.
"""
import argparse, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401
import numpy as np, pandas as pd

def saifi(path):
    rows = []
    for yr in [str(y) for y in range(2015, 2024)]:
        d = pd.read_excel(path, yr, header=None)
        region = None
        for _, r in d.iterrows():
            c0, nm = str(r[0]).strip(), str(r[1]).strip()
            if "REGION" in c0.upper():
                region = c0
            if nm in ("nan", "", "Distribution Utilities"):
                continue
            rows.append(dict(year=int(yr), region=region, du=nm,
                             other=pd.to_numeric(r[4], errors="coerce"),
                             sched=pd.to_numeric(r[7], errors="coerce"),
                             supply=pd.to_numeric(r[10], errors="coerce"),
                             storm=pd.to_numeric(r[13], errors="coerce")))
    df = pd.DataFrame(rows).dropna(subset=["other"])
    df["total"] = df[["other", "sched", "supply", "storm"]].sum(axis=1, min_count=1)
    df["unplanned"] = df[["other", "supply", "storm"]].sum(axis=1, min_count=1)
    r11 = df[df.region.astype(str).str.contains(r"XI \(DAVAO", na=False)]
    print("freq_D4 from ERC SAIFI, Region XI (interruptions/customer/year)")
    for du in sorted(r11.du.unique()):
        s = r11[r11.du == du]
        recent = s[s.year >= 2017]
        print(f"  {du:<10} all-years mean {s.total.mean():6.2f} | "
              f"post-2017 mean {recent.total.mean():6.2f} | "
              f"unplanned {s.unplanned.mean():6.2f}")
    return r11

def phi(path):
    d = pd.read_csv(path, skiprows=1)
    d.columns = [str(c).strip() for c in d.columns]
    c = d[d.iloc[:, 0].astype(str).str.contains("Coconut", na=False)]
    geo = c.columns[1]
    def row(pat):
        m = c[c[geo].astype(str).str.upper().str.contains(pat, na=False)]
        return m.iloc[0] if len(m) else None
    print("\nbuy_cap_frac_phi, first quarter after landfall over same quarter prior year")
    for label, pat, a, b in [
            ("Yolanda 2013, Region VIII", "VIII \\(EASTERN", "2014 Quarter1", "2013 Quarter1"),
            ("Odette 2021, Caraga",       "CARAGA",          "2022 Quarter1", "2021 Quarter1"),
            ("control, Davao / Yolanda",  "XI \\(DAVAO",     "2014 Quarter1", "2013 Quarter1"),
            ("control, Davao / Odette",   "XI \\(DAVAO",     "2022 Quarter1", "2021 Quarter1")]:
        r = row(pat)
        if r is None:
            print(f"  {label:28} region not found"); continue
        x, y = float(r[a]), float(r[b])
        print(f"  {label:28} {x:12,.0f} / {y:12,.0f} = {x/y:.3f}")

def prices(path):
    d = pd.read_csv(path, skiprows=1)
    d.columns = [str(c).strip() for c in d.columns]
    crop, geo = d.columns[0], d.columns[1]
    m = d[(d[crop].astype(str).str.strip() == "Coconut Mature")]
    print("\nw_nut from PSA farmgate (Coconut Mature), 2024-2025 monthly")
    for reg in ["PHILIPPINES", "XI \\(DAVAO"]:
        r = m[m[geo].astype(str).str.upper().str.contains(reg, na=False)]
        if not len(r): continue
        r = r.iloc[0]
        cols = [c for c in d.columns if ("2024" in c or "2025" in c)
                and "Annual" not in c]
        v = pd.to_numeric(pd.Series([r[c] for c in cols]), errors="coerce").dropna()
        v = v[v > 0]
        print(f"  {str(r[geo]).replace('.','').strip():<28} n={len(v):3d} "
              f"mean {v.mean():6.2f} range {v.min():.2f}-{v.max():.2f} "
              f"latest {v.iloc[-1]:.2f} PHP/kg")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="/mnt/project")
    a = ap.parse_args()
    D = pathlib.Path(a.data)
    x = D / "20152023_Reliability_Indices_Summary.xlsx"
    pr = D / "NonFood_and_Industrial_Crops_Volume_of_Production_by_Region_Province_Quarter_and_Semester_20102026.csv"
    fg = D / "Major_Crops_Farmgate_Prices_by_Region_Monthly_20102025.csv"
    if x.exists(): saifi(x)
    else: print(f"missing {x}")
    if pr.exists(): phi(pr)
    else: print(f"missing {pr}")
    if fg.exists(): prices(fg)
    else: print(f"missing {fg}")
    print("\nNOT VERIFIABLE from these sources: w_copra_buy, w_crude, w_vco.")
    print("PSA publishes WHOLE NUT prices; copra is the dried kernel at roughly")
    print("four times the value density, so the copra price cannot be read off")
    print("the nut series without a conversion that is itself an assumption.")
    print("These require PCA price monitoring and remain flagged.")

if __name__ == "__main__":
    main()
