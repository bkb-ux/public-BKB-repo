# Model methodology and audit notes

**Scope:** simplified debt underwriting of a sponsor-backed acquisition of a fictional European mid-market business. EURm unless stated. Financial input assumptions are not sourced to real market transactions.

## 1. Sources & uses

- LTM revenue = €120m, LTM EBITDA = €18m.
- Entry EV = LTM EBITDA × 9.0x = €162m.
- Term debt at close = LTM EBITDA × 5.0x = €90m.
- Uses = purchase EV + transaction fees (€3m) + lender upfront fee (2% × €90m) + €5m funded operating cash = €171.8m.
- Sponsor equity = total uses − new unitranche proceeds = **€81.8m**.
- The lender's initial cash flow is **−€88.2m** because it disburses €90m and earns a €1.8m upfront fee at closing (net cash flow convention). This does not alter the issuer's €90m principal liability.

## 2. Operating model

For each projected year `t`:

```text
Revenue(t)            = Revenue(t-1) × [1 + growth(t)]
EBITDA(t)             = Revenue(t) × EBITDA margin(t)
Depreciation(t)       = Revenue(t) × depreciation rate
EBIT(t)               = EBITDA(t) − depreciation(t)
Cash interest(t)      = Opening unitranche debt(t) × scenario cash interest rate
Cash taxes(t)         = max(0, EBIT(t) − Cash interest(t)) × cash tax rate
NWC(t)                = Revenue(t) × scenario NWC-to-revenue rate
Change in NWC(t)      = NWC(t) − NWC(t-1)
CFADS(t)              = EBITDA(t) − Cash taxes(t) − Capex(t) − Change in NWC(t)
```

CFADS means *cash flow available for debt service* **before cash interest and scheduled amortization**. Tax losses are not carried forward. Depreciation is a simplified tax basis proxy (not identical to capex).

## 3. Debt and cash waterfall

```text
Mandatory repayment(t) = min(opening debt(t), 1% × initial debt)
Cash pre sweep(t)       = opening cash + CFADS − cash interest − mandatory repayment
Available cash(t)      = max(0, cash pre sweep − €5m minimum cash)
Cash sweep(t)          = min(outstanding debt after mandatory, 50% × available cash)
Ending debt(t)         = opening debt − mandatory − sweep
Ending cash(t)         = cash pre sweep − sweep
```

The sweep represents **50% of available year-end cash above a €5m buffer**, not a negotiated excess-cash-flow definition. In actual facilities this is influenced by permitted deductions, leverage step-downs, annual true-up, baskets and unrestricted subsidiaries.

## 4. Credit metrics and tests

```text
Gross leverage      = Ending gross unitranche debt / current year EBITDA
Net leverage        = (Ending debt − max(0, Ending cash)) / current year EBITDA
Cash interest cover = EBITDA / cash interest paid/assumed for year
DSCR                = CFADS / (cash interest + mandatory amortization)
```

At annual testing dates, triggers are: net leverage >6.0x, interest coverage <1.75x or cash <€5m. A `trigger` is *only a modelled test failure*; no automatic bankruptcy, acceleration or legal event of default is inferred.

**Negative ending cash** indicates an unfinanced shortfall. The case projection continues for comparison only; a real capital structure would need a revolver/equity bridge, a waiver, a restructuring or enforcement. Cash shortfalls are explicitly tracked by the cash trigger, not magically funded.

## 5. IRR and MOIC

The performing lender IRR uses the conventional financing cash flow stream:

- time 0: −(funded principal − upfront fee);
- years 1–4: cash interest + principal amortization + sweep;
- year 5: cash interest + mandatory amortization + sweep + outstanding loan principal refinanced at par.

Annual IRR solves NPV = 0 by bisection. This is a **hypothetical performing loan return** and *not* an estimated expected IRR. Interest rates are scenario assumptions and may rise while performance falls; thus a stressed contractual yield can be higher despite a worse credit.

Sponsor terminal equity is floored at zero and approximated as exit enterprise value − remaining unitranche debt + ending positive/negative cash, after a five-year exit at a scenario-dependent exit multiple. No distributions before exit, transaction sale costs or management equity dilution are included.

## 6. Enforcement illustration and recovery

When a test first fails, one possible **illustrative enforcement** scenario is constructed at the end of that annual period:

```text
Net recovery proceeds = scenario-year EBITDA × 5.0x × (1 − 10% enforcement leakage)
Recovery principal    = min(outstanding loan balance, net recovery proceeds)
Recovery percentage   = recovery principal / outstanding loan balance
```

The simplified enforcement lender IRR assumes contractual interest and scheduled principal payments through that year, followed by recovery of remaining principal. **This can overestimate realistic recovery if interest payments are missed or enforcement takes more than one year.** No intercreditor waterfall, security enforcement timing, fees on stressed claims, competing priority liens, withholding taxes, court jurisdiction or actual collateral is modeled. A covenant trigger does not cause this event automatically.

The recovery sensitivity stresses EBITDA by −10%, −20%, −30%, −40% and going-concern enterprise multiples of 3.0x–7.0x with 10% leakage. The claim and reference EBITDA are those in the severe case at first trigger, or maturity if no trigger occurs.

## 7. Debt sizing and refinancing

A leverage-sensitivity table reruns Base and Downside with entry debt from 3.5x to 6.0x, reflecting altered sponsor equity funding of the same acquisition EV. The 5-year refinancing capacity screen assumes only 4.5x of terminal EBITDA can be refinanced at maturity. It is a rough credit-sizing screen, not an executable financing commitment.

## 8. Key limitations and next extensions

- Annual rather than monthly or quarterly financial forecast.
- One unitranche with no super-senior RCF, payment-in-kind, commitment fee, hedging, floating base-rate floor or annual OID amortization.
- No three-statement balance sheet integration or cash accounting reconciliation.
- EBITDA ignores acquisition adjustments, restructuring provisions and detailed segment contribution.
- Taxes simplified; no interest deductibility caps, tax loss carryforwards or tax jurisdiction effects.
- Cash sweep approximation differs from signed legal documentation.
- Static first-trigger enforcement rather than probability-weighted credit loss; no expected loss, PD/LGD calibration or exposure at default.
- Simple gross refinancing capacity and exit EV; not bankable forecasts or market forecasts.

These limitations are deliberate and are disclosed to make the repo appropriate for a junior analyst **portfolio case study**, not to imply production-ready or real-money underwriting.