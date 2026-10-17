import copy
import math
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from private_credit.model import (
    annual_irr, build_sources_uses, leverage_sensitivity, load_assumptions,
    project, recovery_matrix, validate_assumptions
)

A = load_assumptions(Path(__file__).resolve().parents[1] / "data" / "assumptions.json")


def test_sources_equal_uses():
    s = build_sources_uses(A)
    assert math.isclose(s["TOTAL SOURCES"], s["TOTAL USES"])
    assert s["Sponsor equity"] > 0
    assert math.isclose(s["Lender upfront fee"], 1.8)


def test_sources_include_funded_cash_not_subtract_it():
    s = build_sources_uses(A)
    assert math.isclose(s["Sponsor equity"], 81.8, abs_tol=1e-8)


@pytest.mark.parametrize("scenario", ["Base", "Downside", "Severe Downside"])
def test_balance_rollforward_and_cash_bridge(scenario):
    r = project(A, scenario)
    s = r.schedule
    for _, x in s.iterrows():
        assert x["Ending debt"] >= 0
        assert math.isclose(x["Ending debt"], x["Opening debt"]-x["Mandatory amortization"]-x["Cash sweep"], abs_tol=1e-8)
        assert math.isclose(x["Ending cash"], x["Opening cash"]+x["CFADS"]-x["Cash interest"]-x["Mandatory amortization"]-x["Cash sweep"], abs_tol=1e-8)
        assert x["Cash sweep"] <= x["Opening debt"] - x["Mandatory amortization"] + 1e-8


def test_base_no_trigger_and_deleverages():
    r = project(A, "Base")
    assert r.summary["First covenant / cash trigger year"] is None
    assert r.summary["Year 5 debt"] < r.summary["Initial unitranche"]


def test_severe_has_trigger_and_recovery_loss():
    r = project(A, "Severe Downside")
    assert r.summary["First covenant / cash trigger year"] is not None
    assert 0 <= r.summary["Illustrative enforcement recovery pct"] < 1
    assert r.summary["Illustrative enforcement lender IRR"] < r.summary["Performing lender IRR"]


def test_downside_worse_interest_coverage():
    assert project(A, "Downside").summary["Min interest coverage"] < project(A, "Base").summary["Min interest coverage"]


def test_irr_simple_example():
    assert math.isclose(annual_irr([-100, 110]), 0.10, abs_tol=1e-10)


def test_recovery_bounded_and_monotone():
    m = recovery_matrix(90, 18)
    cols = [c for c in m if c.endswith("recovery")]
    for col in cols:
        assert m[col].between(0, 1).all()
    assert all(m["7.0x recovery"] >= m["3.0x recovery"])
    assert m["5.0x recovery"].iloc[0] >= m["5.0x recovery"].iloc[-1]


def test_sensitivity_increasing_leverage_deteriorates_coverage():
    df = leverage_sensitivity(A)
    base = df[df["Scenario"] == "Base"]
    assert base.iloc[0]["Min ICR"] > base.iloc[-1]["Min ICR"]


def test_invalid_scenario_lengths_rejected():
    bad = copy.deepcopy(A)
    bad["scenarios"]["Base"]["revenue_growth"] = [0.05]
    with pytest.raises(AssertionError):
        validate_assumptions(bad)


def test_loan_size_sensitivity():
    lower = copy.deepcopy(A)
    lower["transaction"]["entry_debt_ebitda"] = 4.0
    higher = copy.deepcopy(A)
    higher["transaction"]["entry_debt_ebitda"] = 5.5
    assert project(lower, "Base").summary["Min interest coverage"] > project(higher, "Base").summary["Min interest coverage"]