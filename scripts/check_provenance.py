"""scripts/check_provenance.py — provenance ledger validator (§9.2 enforcement).

Two jobs:
  1) SYNC: every numeric `value` in provenance.yaml that names a PlantParams field
     must equal the code value — catches ledger drift when a parameter is tuned
     but its provenance entry is not updated (silent-substitution guard).
  2) GATE: report counts by status; --strict exits non-zero if any parameter feeding
     an E11-weighted claim is still unverified (the flag a manuscript build checks).

Deliberately dependency-light: parses the YAML subset used here without pyyaml
(available everywhere; no new dependency). Usage:
    python scripts/check_provenance.py            # report
    python scripts/check_provenance.py --strict   # manuscript gate
"""
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core.plant_dae import PlantParams


def parse_params(text):
    """Minimal parser for the `parameters:` block: name -> {key: value}. Handles
    both block and inline-brace entries used in provenance.yaml."""
    out, cur = {}, None
    body = text.split("parameters:", 1)[1]
    # join brace entries that wrap across lines into one logical line first
    lines = []
    buf = None
    for raw in body.splitlines():
        if buf is not None:
            buf += " " + raw.strip()
            if "}" in raw:
                lines.append(buf); buf = None
            continue
        if re.match(r"^  [A-Za-z0-9_]+:\s*\{", raw) and "}" not in raw:
            buf = raw.rstrip()
        else:
            lines.append(raw)
    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        m_block = re.match(r"^  ([A-Za-z0-9_]+):\s*$", line)
        m_inline = re.match(r"^\s*([A-Za-z0-9_]+):\s*\{(.+)\}\s*$", line)
        if m_inline:
            name, inner = m_inline.groups()
            d = {}
            for part in re.split(r",\s*(?=[a-z_]+:)", inner):
                if ":" in part:
                    k, v = part.split(":", 1)
                    d[k.strip()] = v.strip().strip('"')
            out[name] = d
            cur = None
        elif m_block:
            cur = m_block.group(1); out[cur] = {}
        elif cur:
            # block-style "key: value; key: value" possibly split across lines
            for seg in line.split(";"):
                if ":" in seg:
                    k, v = seg.split(":", 1)
                    out[cur][k.strip()] = v.strip().strip('"')
    return out


def as_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main(strict=False):
    text = pathlib.Path("provenance.yaml").read_text()
    params = parse_params(text)
    p = PlantParams()

    # ---- SYNC ----
    field_map = {  # provenance name -> PlantParams attribute
        "w_vco": "w_vco", "w_crude": "w_crude", "w_meal": "w_meal",
        "w_char": "w_char", "w_conc": "w_conc", "w_shell": "w_shell",
        "w_copra_buy": "w_copra_buy", "w_copra_sale": "w_copra_sale",
        "w_fuel_offset": "w_fuel_offset", "w_nut": "w_nut",
        "f_kernel": "f_kernel", "f_shell": "f_shell", "f_husk": "f_husk",
        "f_water": "f_water", "y_oil": "y_oil", "y_wet": "y_wet",
        "y_refine": "y_refine", "y_char": "y_char",
        "cap_press": "cap_press", "cap_refine": "cap_refine",
        "I_crude_max": "I_crude_max",
    }
    drift = []
    for pv_name, attr in field_map.items():
        pv = as_float(params.get(pv_name, {}).get("value"))
        code = float(getattr(p, attr))
        if pv is None or abs(pv - code) > 1e-9:
            drift.append(f"  {pv_name}: ledger={pv} code={code}")
    if drift:
        print("SYNC FAIL — provenance.yaml out of step with code:")
        print("\n".join(drift)); sys.exit(2)
    print(f"SYNC OK: {len(field_map)} code-backed parameters match ledger")

    # ---- GATE ----
    total = len(params)
    verified = sum(1 for d in params.values() if d.get("verified") == "true")
    hi = [n for n, d in params.items()
          if d.get("e11_weight") == "hi" and d.get("verified") != "true"]
    print(f"provenance: {total} params | verified {verified}/{total} | "
          f"E11-critical unverified: {len(hi)}")
    for n in hi:
        src = params[n].get("source", "?")
        print(f"  [hi] {n}: {src[:64]}")
    if strict and (verified < total):
        print(f"\nSTRICT GATE: {total - verified} unverified — "
              "not manuscript-ready (§9.2)")
        sys.exit(1)


if __name__ == "__main__":
    main("--strict" in sys.argv)
