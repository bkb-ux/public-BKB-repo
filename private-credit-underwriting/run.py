"""Rebuild every derived table, chart and memo from source assumptions.

Usage:
    python run.py
    python run.py --assumptions data/assumptions.json --output outputs
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from private_credit.model import (
    build_sources_uses, leverage_sensitivity, load_assumptions, project, recovery_matrix
)


def format_pct(x):
    if pd.isna(x):
        return "n/a"
    return f"{x*100:.1f}%"


def build_ic_memo(results: dict, sensitivity: pd.DataFrame, out: Path) -> str:
    a, b, c = (results[k].summary for k in ("Base", "Downside", "Severe Downside"))
    base_su = results["Base"].sources_uses
    moderate_clean = b["First covenant / cash trigger year"] is None
    severe_trigger = c["First covenant / cash trigger year"]
    decision = "CONDITIONAL APPROVAL — subject to diligence and tighter protections" if moderate_clean else "HOLD — downside case requires restructuring of terms"
    memo = f"""# Investment Committee Memo — Atlas Industrial Services

> **Educational / fictional case.** Automatically generated from `data/assumptions.json`. EUR millions unless stated. Not a real investment recommendation.

## Preliminary recommendation
**{decision}**

The contemplated **€{a['Initial unitranche']:.1f}m senior secured unitranche** is sized at **{a['Entry debt / EBITDA']:.1f}x LTM EBITDA**. The base case generates cash deleveraging. The moderate downside {'remains within the modelled tests' if moderate_clean else 'breaches at least one modelled test'}, while the severe downside first triggers a covenant or minimum-cash test in **Year {severe_trigger if severe_trigger is not None else 'none'}**. This is *not* automatic proof of bankruptcy: the model separately illustrates a hypothetical immediate enforcement outcome.

## 1 | Borrower and sponsor thesis
Atlas Industrial Services is a **fictional** mid-market provider of outsourced industrial maintenance and inspection. Assumed strengths: contract recurrence, diversified clients and maintenance-critical services. None of these business characteristics have been independently verified; the diligence programme must establish them.

## 2 | Transaction and sources & uses

| Uses | €m | Sources | €m |
|---|---:|---|---:|
| Enterprise purchase price | {base_su['Enterprise purchase price (cash-free/debt-free)']:.1f} | Unitranche loan | {base_su['New unitranche facility']:.1f} |
| Transaction fees | {base_su['Transaction fees']:.1f} | Sponsor equity | {base_su['Sponsor equity']:.1f} |
| Lender upfront fee | {base_su['Lender upfront fee']:.1f} | | |
| Cash at closing | {base_su['Cash funded at close']:.1f} | | |
| **Total uses** | **{base_su['TOTAL USES']:.1f}** | **Total sources** | **{base_su['TOTAL SOURCES']:.1f}** |

The model assumes a debt-free/cash-free purchase price. Cash at close is *newly funded* and included in transaction uses. No vendor rollover or pre-existing debt is assumed.

## 3 | Investment case by scenario

| Credit metric | Base | Downside | Severe downside |
|---|---:|---:|---:|
| Year 5 debt (€m) | {a['Year 5 debt']:.1f} | {b['Year 5 debt']:.1f} | {c['Year 5 debt']:.1f} |
| Year 5 net leverage | {a['Year 5 net leverage']:.2f}x | {b['Year 5 net leverage']:.2f}x | {c['Year 5 net leverage']:.2f}x |
| Minimum cash interest coverage | {a['Min interest coverage']:.2f}x | {b['Min interest coverage']:.2f}x | {c['Min interest coverage']:.2f}x |
| Minimum DSCR | {a['Min DSCR']:.2f}x | {b['Min DSCR']:.2f}x | {c['Min DSCR']:.2f}x |
| Minimum ending cash (€m) | {a['Min liquidity']:.1f} | {b['Min liquidity']:.1f} | {c['Min liquidity']:.1f} |
| First covenant/cash trigger | {a['First covenant / cash trigger year'] or 'None'} | {b['First covenant / cash trigger year'] or 'None'} | {c['First covenant / cash trigger year'] or 'None'} |
| Performing IRR (assumes par refi) | {format_pct(a['Performing lender IRR'])} | {format_pct(b['Performing lender IRR'])} | {format_pct(c['Performing lender IRR'])} |
| 5Y refinance capacity vs debt | {'Pass' if a['Maturity coverage by refi debt capacity'] else 'Fail'} | {'Pass' if b['Maturity coverage by refi debt capacity'] else 'Fail'} | {'Pass' if c['Maturity coverage by refi debt capacity'] else 'Fail'} |

**Interpretation.** Performing lender IRR is a *conditional contractual return*, including a 2% upfront fee and full par repayment at maturity. It should not be interpreted as expected return, especially once a trigger has occurred.

## 4 | Loan structure and covenant design
- Senior secured **unitranche**, modelled as a single claim (no intercreditor or revolver waterfall).
- **7.5% floating/cash coupon assumed fixed within each scenario**, with +200bp and +300bp interest stress.
- **1% annual mandatory amortisation** of original principal; **50% sweep** of modelled surplus above minimum cash (simplified, not a legal ECF definition).
- Springing testing is **not** assumed: annual max net leverage **6.0x**, minimum EBITDA-to-cash-interest **1.75x**, minimum cash **€5m**.
- Formal covenant terms, baskets, cure rights, add-backs, equity cures, permitted debt and information rights remain to be negotiated; covenant breach is **not necessarily an event of default**.

## 5 | Key credit risks and mitigants
1. **Earnings pressure / cost rigidity:** request contract-level retention, volume-price bridge and customer concentration data; cap EBITDA add-backs.
2. **Floating-rate burden:** examine hedging terms, ICR headroom and payment capacity at +200 to +300bps.
3. **Liquidity:** test monthly working-capital seasonality, tax calendars and maintenance capex; require a funded liquidity buffer and rolling 13-week cash report if distressed.
4. **Re-financing / maturity:** five-year refinance capacity is a *simplified* 4.5x terminal EBITDA benchmark; run lender market / credit-spread sensitivities before approval.
5. **Enforcement and recovery:** confirm lien perfection, corporate guarantees, collateral value and structural subordination; the simple EV-based recovery is not a legal waterfall.

## 6 | Recovery and severe downside
In the severe downside, the illustrative enforcement outcome following the first trigger is **{format_pct(c['Illustrative enforcement recovery pct']) if c['Illustrative enforcement recovery pct'] is not None else 'not applicable'}** of outstanding principal and a simplified lender IRR of **{format_pct(c['Illustrative enforcement lender IRR']) if c['Illustrative enforcement lender IRR'] is not None else 'not applicable'}**. This assumes resolution at the first annual trigger, collection of that year's coupons/principal and a **5.0x EBITDA enforcement multiple net of 10% costs**. It is illustrative, not a forecast of default probability, LGD or legal recovery.

## 7 | Final conditions precedent / open questions
- Obtain audited historical accounts, full quality-of-earnings report and normalized EBITDA bridge.
- Verify customer retention, backlog, pricing power and exposure to cyclical end-markets.
- Validate maintenance vs growth capex and seasonal net working capital.
- Confirm debt documentation: maintenance covenants, cure provisions, collateral and ranking.
- Commission independent business plan and ensure sponsor equity funds all required uses.
- Re-run sizing at reduced leverage if diligence uncovers weaker cash conversion or thinner covenant headroom.

**Verdict:** Preliminary and conditional only. No real capital should be committed on fictional assumptions alone.
"""
    out.write_text(memo, encoding="utf-8")
    return decision


def make_plots(results: dict, out: Path) -> None:
    chart_dir = out / "charts"
    chart_dir.mkdir(parents=True, exist_ok=True)
    for metric, filename, ylabel in (
        ("Net leverage", "net_leverage.png", "Net debt / EBITDA (x)"),
        ("EBITDA / cash interest", "interest_coverage.png", "EBITDA / interest (x)"),
        ("Ending debt", "debt_outstanding.png", "Unitranche debt (€m)"),
    ):
        fig, ax = plt.subplots(figsize=(8.8, 4.5))
        for name, case in results.items():
            ax.plot(case.schedule["Year"], case.schedule[metric], marker="o", label=name)
        ax.set_xlabel("Projected year")
        ax.set_ylabel(ylabel)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.grid(axis="y", alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(chart_dir / filename, dpi=170)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Rebuild fictional private credit underwriting case")
    parser.add_argument("--assumptions", type=Path, default=ROOT / "data" / "assumptions.json")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    a = load_assumptions(args.assumptions)
    results = {name: project(a, name) for name in a["scenarios"]}
    for name, case in results.items():
        case.schedule.to_csv(out / f"{name.lower().replace(' ', '_')}_schedule.csv", index=False)
    summary_df = pd.DataFrame([case.summary for case in results.values()])
    summary_df.to_csv(out / "scenario_summary.csv", index=False)
    pd.DataFrame(list(build_sources_uses(a).items()), columns=["Sources or uses", "EURm"]).to_csv(
        out / "sources_and_uses.csv", index=False)
    sensitivity = leverage_sensitivity(a)
    sensitivity.to_csv(out / "leverage_sensitivity.csv", index=False)
    severe = results["Severe Downside"]
    first_trigger = severe.summary["First covenant / cash trigger year"]
    row = (severe.schedule.iloc[first_trigger - 1] if first_trigger else severe.schedule.iloc[-1])
    recovery_matrix(
        claim=float(row["Ending debt"]),
        reference_ebitda=float(row["EBITDA"]),
        leakage_pct=a["recovery"]["enforcement_leakage_pct"],
    ).to_csv(out / "recovery_sensitivity.csv", index=False)
    make_plots(results, out)
    memo_path = ROOT / "docs" / "investment_memo.md"
    decision = build_ic_memo(results, sensitivity, memo_path)
    print("Generated outputs in", out)
    print("Recommendation:", decision)
    print(summary_df[["Scenario", "Year 5 net leverage", "Min interest coverage", "Min DSCR", "First covenant / cash trigger year"]].to_string(index=False))


if __name__ == "__main__":
    main()