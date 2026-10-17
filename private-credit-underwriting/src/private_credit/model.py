"""Illustrative senior-secured private-credit underwriting engine.

Monetary amounts are in millions. Assumptions and company are fictional.
All principal recovery / enforcement outputs are *scenarios*, not forecasts.
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class CaseResult:
    scenario: str
    schedule: pd.DataFrame
    summary: dict[str, Any]
    sources_uses: dict[str, float]


def load_assumptions(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        a = json.load(handle)
    validate_assumptions(a)
    return a


def validate_assumptions(a: dict) -> None:
    hist, tr, loan, ops, cov = [a[k] for k in (
        "historic", "transaction", "unitranche", "operations", "covenants")]
    assert hist["revenue"] > 0 and hist["ebitda"] > 0, "Positive historic revenue and EBITDA required"
    assert hist["ebitda"] <= hist["revenue"], "EBITDA cannot exceed revenue in this simplified model"
    assert tr["entry_ev_ebitda"] > 0 and tr["entry_debt_ebitda"] >= 0
    assert 0 <= loan["cash_interest_rate"] < 1
    for name in ("upfront_fee", "mandatory_amortization_pct_initial", "excess_cash_flow_sweep_pct"):
        assert 0 <= loan[name] <= 1, f"Invalid {name}"
    assert 0 <= ops["tax_rate"] < 1
    assert cov["min_cash"] >= 0 and tr["opening_cash"] >= 0
    assert loan["maturity_year"] >= 1
    for name, scenario in a["scenarios"].items():
        n = loan["maturity_year"]
        assert len(scenario["revenue_growth"]) == n, f"{name}: growth length != maturity"
        assert len(scenario["ebitda_margin"]) == n, f"{name}: margin length != maturity"
        assert all(x > -1 for x in scenario["revenue_growth"]), f"{name}: invalid revenue growth"
        assert all(0 < x < 1 for x in scenario["ebitda_margin"]), f"{name}: invalid EBITDA margin"
        assert loan["cash_interest_rate"] + scenario["interest_rate_change"] > 0


def annual_irr(cashflows: list[float]) -> float:
    """Bisection IRR for conventional lending flows (one initial outflow)."""
    if not cashflows or cashflows[0] >= 0 or not any(x > 0 for x in cashflows[1:]):
        return float("nan")

    def npv(rate: float) -> float:
        return sum(cf / (1.0 + rate) ** i for i, cf in enumerate(cashflows))

    lo, hi = -0.999, 10.0
    if npv(lo) * npv(hi) > 0:
        return float("nan")
    for _ in range(180):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def build_sources_uses(a: dict) -> dict[str, float]:
    h, t, loan = a["historic"], a["transaction"], a["unitranche"]
    ev = h["ebitda"] * t["entry_ev_ebitda"]
    gross_loan = h["ebitda"] * t["entry_debt_ebitda"]
    financing_fee = gross_loan * loan["upfront_fee"]
    uses = ev + t["transaction_fees"] + financing_fee + t["opening_cash"]
    equity = uses - gross_loan
    if equity < 0:
        raise ValueError("Negative sponsor equity: invalid sources and uses")
    s = {
        "Enterprise purchase price (cash-free/debt-free)": ev,
        "Transaction fees": t["transaction_fees"],
        "Lender upfront fee": financing_fee,
        "Cash funded at close": t["opening_cash"],
        "TOTAL USES": uses,
        "New unitranche facility": gross_loan,
        "Sponsor equity": equity,
        "TOTAL SOURCES": gross_loan + equity,
    }
    assert math.isclose(s["TOTAL USES"], s["TOTAL SOURCES"], abs_tol=1e-8)
    return s


def project(a: dict, scenario_name: str) -> CaseResult:
    validate_assumptions(a)
    s = a["scenarios"][scenario_name]
    h, t, loan, ops, cov, rec = [a[k] for k in (
        "historic", "transaction", "unitranche", "operations", "covenants", "recovery")]
    sources_uses = build_sources_uses(a)
    initial_debt = sources_uses["New unitranche facility"]
    opening_cash = t["opening_cash"]
    revenue, debt, cash = h["revenue"], initial_debt, opening_cash
    nwc = revenue * ops["base_nwc_pct_revenue"]
    lender_flows = [-initial_debt + sources_uses["Lender upfront fee"]]
    rows = []

    for year in range(1, loan["maturity_year"] + 1):
        g, m = s["revenue_growth"][year-1], s["ebitda_margin"][year-1]
        rev_bop, debt_bop, cash_bop, nwc_bop = revenue, debt, cash, nwc
        revenue = rev_bop * (1 + g)
        ebitda = revenue * m
        depreciation = revenue * ops["depreciation_pct_revenue"]
        ebit = ebitda - depreciation
        interest_rate = loan["cash_interest_rate"] + s["interest_rate_change"]
        interest = debt_bop * interest_rate  # BOP convention, no circularity
        capex = revenue * (ops["base_capex_pct_revenue"] + s["capex_pct_revenue_change"])
        nwc = revenue * (ops["base_nwc_pct_revenue"] + s["nwc_pct_revenue_change"])
        delta_nwc = nwc - nwc_bop
        cash_taxes = max(0.0, ebit - interest) * ops["tax_rate"]
        cfads = ebitda - cash_taxes - capex - delta_nwc
        mandatory = min(debt_bop, initial_debt * loan["mandatory_amortization_pct_initial"])
        cash_after_contractual_service = cash_bop + cfads - interest - mandatory
        # Sweep 50% of year-end available cash above the minimum operating buffer.
        # Note this is an illustrative excess-cash calculation, not a legal ECF definition.
        available_to_sweep = max(0.0, cash_after_contractual_service - cov["min_cash"])
        sweep = min(debt_bop - mandatory, available_to_sweep * loan["excess_cash_flow_sweep_pct"])
        debt = max(0.0, debt_bop - mandatory - sweep)
        cash = cash_after_contractual_service - sweep
        net_debt = debt - max(0.0, cash)  # excludes negative cash as an offset
        gross_lev = debt / ebitda
        net_lev = net_debt / ebitda
        coverage = ebitda / interest if interest else float("inf")
        dscr = cfads / (interest + mandatory) if interest + mandatory else float("inf")
        lever_breach = net_lev > cov["max_net_leverage"]
        icr_breach = coverage < cov["min_ebitda_interest_coverage"]
        cash_breach = cash < cov["min_cash"]
        lender_flows.append(interest + mandatory + sweep)
        rows.append({
            "Year": year, "Revenue": revenue, "Revenue growth": g,
            "EBITDA": ebitda, "EBITDA margin": m, "Depreciation": depreciation,
            "EBIT": ebit, "Cash interest": interest, "Cash taxes": cash_taxes,
            "Capex": capex, "Net working capital": nwc, "Change in NWC": delta_nwc,
            "CFADS": cfads, "Opening cash": cash_bop,
            "Opening debt": debt_bop, "Mandatory amortization": mandatory,
            "Cash sweep": sweep, "Ending debt": debt, "Ending cash": cash,
            "Gross leverage": gross_lev, "Net leverage": net_lev,
            "EBITDA / cash interest": coverage, "DSCR": dscr,
            "Net leverage headroom": cov["max_net_leverage"] - net_lev,
            "ICR headroom": coverage - cov["min_ebitda_interest_coverage"],
            "Liquidity headroom": cash - cov["min_cash"],
            "Leverage breach": lever_breach, "ICR breach": icr_breach,
            "Cash breach": cash_breach,
            "Any trigger": lever_breach or icr_breach or cash_breach,
        })

    schedule = pd.DataFrame(rows)
    end = schedule.iloc[-1]
    performing_flows = lender_flows.copy()
    performing_flows[-1] += end["Ending debt"]  # contractual refinancing at maturity
    performing_irr = annual_irr(performing_flows)
    performing_moic = sum(performing_flows[1:]) / -performing_flows[0]

    # Covenant test failure is NOT necessarily acceleration, insolvency or default.
    # A conditional enforcement illustration assumes immediate resolution at first trigger
    # with interest and scheduled principal received through that year.
    triggers = schedule[schedule["Any trigger"]]
    trigger_year = int(triggers.iloc[0]["Year"]) if len(triggers) else None
    recovery_amount = None
    recovery_pct = None
    enforcement_irr = None
    if trigger_year is not None:
        row = triggers.iloc[0]
        net_asset_proceeds = max(0.0, row["EBITDA"] * rec["illustrative_enforcement_multiple"]
                                 * (1 - rec["enforcement_leakage_pct"]))
        recovery_amount = min(row["Ending debt"], net_asset_proceeds)
        recovery_pct = recovery_amount / row["Ending debt"] if row["Ending debt"] else 1.0
        enforcement_flows = lender_flows[:trigger_year + 1]
        enforcement_flows[-1] += recovery_amount
        enforcement_irr = annual_irr(enforcement_flows)

    exit_ev = end["EBITDA"] * max(0.0, t["exit_ev_ebitda"] + s["exit_multiple_change"])
    sponsor_terminal_equity = max(0.0, exit_ev - end["Ending debt"] + end["Ending cash"])
    sponsor_equity = sources_uses["Sponsor equity"]
    gross_refi_capacity = max(0.0, end["EBITDA"] * rec["refinance_multiple"])
    summary = {
        "Scenario": scenario_name,
        "Initial unitranche": initial_debt,
        "Sponsor equity": sponsor_equity,
        "Entry debt / EBITDA": initial_debt / h["ebitda"],
        "Year 5 EBITDA": end["EBITDA"],
        "Year 5 debt": end["Ending debt"],
        "Year 5 cash": end["Ending cash"],
        "Year 5 net leverage": end["Net leverage"],
        "Debt paydown pct": 1 - end["Ending debt"] / initial_debt,
        "Min interest coverage": schedule["EBITDA / cash interest"].min(),
        "Min DSCR": schedule["DSCR"].min(),
        "Min liquidity": schedule["Ending cash"].min(),
        "First covenant / cash trigger year": trigger_year,
        "Performing lender IRR": performing_irr,
        "Performing lender MOIC": performing_moic,
        "Illustrative enforcement recovery pct": recovery_pct,
        "Illustrative enforcement lender IRR": enforcement_irr,
        "Exit enterprise value": exit_ev,
        "Sponsor equity terminal value": sponsor_terminal_equity,
        "Sponsor MOIC (no distributions)": sponsor_terminal_equity / sponsor_equity,
        "Year 5 refinancing debt capacity (4.5x EBITDA)": gross_refi_capacity,
        "Maturity coverage by refi debt capacity": gross_refi_capacity >= end["Ending debt"],
    }
    return CaseResult(scenario_name, schedule, summary, sources_uses)


def recovery_matrix(claim: float, reference_ebitda: float,
                    ebitda_haircuts=(0.10, 0.20, 0.30, 0.40),
                    ev_multiples=(3.0, 4.0, 5.0, 6.0, 7.0),
                    leakage_pct=0.10) -> pd.DataFrame:
    """Simple going-concern EV allocation to a single secured debt class."""
    records = []
    for haircut in ebitda_haircuts:
        row = {"EBITDA haircut": haircut, "Stressed EBITDA": reference_ebitda * (1 - haircut)}
        for multiple in ev_multiples:
            enterprise_value = row["Stressed EBITDA"] * multiple
            available = max(0.0, enterprise_value * (1 - leakage_pct))
            row[f"{multiple:.1f}x recovery"] = min(1.0, available / claim) if claim > 0 else 1.0
        records.append(row)
    return pd.DataFrame(records)


def leverage_sensitivity(a: dict, leverage_levels=(3.5, 4, 4.5, 5, 5.5, 6)) -> pd.DataFrame:
    rows = []
    for lev in leverage_levels:
        altered = copy.deepcopy(a)
        altered["transaction"]["entry_debt_ebitda"] = lev
        for name in ("Base", "Downside"):
            result = project(altered, name)
            rows.append({
                "Entry debt / EBITDA": lev,
                "Scenario": name,
                "Min DSCR": result.summary["Min DSCR"],
                "Min ICR": result.summary["Min interest coverage"],
                "Year 5 net leverage": result.summary["Year 5 net leverage"],
                "First trigger year": result.summary["First covenant / cash trigger year"],
                "Min liquidity": result.summary["Min liquidity"],
            })
    return pd.DataFrame(rows)