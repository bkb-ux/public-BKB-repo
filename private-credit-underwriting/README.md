# Private Credit Underwriting & LBO Model

**An end-to-end, Python-based senior-secured unitranche underwriting case study.**  
**Fictional borrower · €m · 5-year forecast · Investment Committee memo**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-lightgrey)

> **Important:** Atlas Industrial Services, its financial statements, the proposed financing and all market parameters in this repository are fictional educational inputs. No actual borrower, transaction, employer data or investment advice is involved.

## The credit question

Would you underwrite a **€90m senior-secured unitranche** for a hypothetical industrial maintenance business with €18m LTM EBITDA — and how would that view change if margins compress, revenue falls and rates rise?

The model analyses **borrower debt-service capacity and lender downside protection**, not just the return on the sponsor's equity investment.

## Key metrics from the model

| Metric | Base | Downside | Severe downside |
|---|---:|---:|---:|
| Entry gross leverage | 5.0x | 5.0x | 5.0x |
| Year-5 net leverage | 1.89x | 3.56x | 5.55x |
| Minimum EBITDA / cash interest | 2.80x | 1.89x | 1.31x |
| Minimum DSCR | 1.67x | 1.08x | 0.75x |
| First covenant / liquidity test failure | None | None | Year 1 |
| Refinancing capacity test at maturity | Pass | Pass | Fail |

**Preliminary conclusion: CONDITIONAL APPROVAL**, subject to diligence and stronger documentary protection. In the severe case, a trigger prompts an *illustrative* enforcement scenario, not an automatic legal default.

For assumptions, caveats and credit conclusion, read the [Investment Committee memo](docs/investment_memo.md).

## Visual credit analysis

Run `python run.py` locally to generate the net-leverage chart.

Run `python run.py` locally to generate the interest-coverage chart.

Run `python run.py` locally to generate the debt-outstanding chart.

## What is included?

1. **Sources & uses**: cash-free/debt-free enterprise purchase price, lender upfront fee, transaction fees, new funded cash and sponsor equity.
2. **Operating forecast**: five years of revenue, EBITDA margins, depreciation, capex, net working capital and cash taxes.
3. **Debt schedule**: annual beginning debt, interest, mandatory amortization, modeled excess cash-flow sweep and ending debt.
4. **Coverage and covenants**: gross/net leverage, EBITDA/cash interest, debt service coverage, cash headroom and first trigger year.
5. **Scenarios and sensitivity**: base, downside, severe downside; debt sizing at entry leverage of 3.5x–6.0x; lender recovery across EBITDA haircuts and enterprise-value multiples.
6. **Investor analytics**: performing lender IRR and MOIC, sponsor MOIC, maturity refinancing screen and a conditional enforcement illustration.
7. **Investment Committee memo** with an underwriting recommendation, transaction summary, key risks, mitigants and diligence questions.
8. **Reproducible outputs**, 13 unit tests and a GitHub Actions workflow.

## Quick start

```bash
# Python 3.11+ recommended
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
python -m pytest -q
```

On execution, `run.py` reads `data/assumptions.json` and regenerates the tables, three charts and investment memo. No private datasets, paid market feeds or credentials are needed.

```bash
# Use alternative assumption set and/or output folder
python run.py --assumptions data/assumptions.json --output outputs
```

**Modify only the input JSON**, then re-run the model; never edit the derived CSV tables manually.

## Repository layout

```text
private-credit-underwriting/
├── ../.github/workflows/private-credit-tests.yml # CI runs tests + rebuild
├── data/assumptions.json             # Editable underwriting inputs
├── docs/
│   ├── investment_memo.md           # Generated from model results
│   ├── methodology.md               # Equations, model conventions, caveats
│   └── term_sheet.md                # Illustrative proposed documentation
├── outputs/
│   ├── charts/                      # Three generated PNG charts
│   ├── *_schedule.csv               # Debt & financial forecast per scenario
│   ├── scenario_summary.csv
│   ├── sources_and_uses.csv
│   ├── leverage_sensitivity.csv
│   └── recovery_sensitivity.csv
├── src/private_credit/model.py       # Calculation engine
├── tests/test_model.py              # 13 automated tests
├── run.py                           # Reproducible entry point
├── requirements.txt
└── LICENSE
```

## Methodological caveats

- **Illustrative, not production-grade**: simplified single-tranche capital structure, annual periods, no seasonal funding, detailed debt documentation, actual accounting statements or probability-weighted expected losses.
- **Debt yield is not expected return**: the contractual lender IRR assumes full par takeout at maturity, even in a scenario in which a covenant trigger occurs. The separate enforcement IRR makes different assumptions.
- **Trigger is not automatic default**: breaches may be cured, waived or amended, depending on signed agreements.
- **Recovery is not a legal waterfall**: enterprise value × stressed EBITDA multiple less a flat enforcement-cost allowance, capped by the claim. No lien verification, guarantor structure, revolver priority or creditor-ranking analysis is modeled.
- **Stressed negative cash means an unfinanced liquidity shortfall**, not a permissible ongoing cash balance. The annual forecast continues pro forma for comparison; a real lender would require a liquidity fix or restructuring before then.
- **Proceeds timing is simplified**: annual cash flows, BOP interest, EOY repayments, assumed receipt of contracted interest and scheduled amortization through the illustrative trigger year.

For full methodology, see [Methodology](docs/methodology.md).

## Testing

```bash
python -m pytest -q
```

Checks include sources-and-uses reconciliation, cash/debt roll-forwards, non-negative loan balance, covenants, IRR, monotonic recovery behavior and leverage-sizing sensitivity. Continuous integration is defined in the repository root `.github/workflows/private-credit-tests.yml` and runs on pushes/PRs after publication.

## Interview discussion prompts

- Why choose 5.0x leverage rather than 4.0x or 5.5x?
- Under which downside case does cash interest become unsustainable?
- How is an EBITDA add-back different from realized cash flow?
- What protections would you negotiate if the borrower has highly seasonal working capital?
- Why can the contractual lender IRR increase in the downside while expected credit performance deteriorates?
- What changes if a super-senior RCF is introduced ahead of unitranche lenders?

## Licensing

MIT software license. Educational and illustrative material, not an offer to lend or invest.