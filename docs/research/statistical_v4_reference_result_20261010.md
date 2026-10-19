# V4 finite-family reference result

Role: GATE. Status: ACCEPTED_WITH_RISK for saved aggregation only.
Separate Hooke review verified the exact108cell grid, identities, all Wilson
upper bounds and reported power counts without rerunning simulation. No blockers.
No market inference, CMC scoring, strategy selection or profitability claim.

Separate Hooke reviews accepted the contract, reference implementation/artifacts
and confirmation runner WITH RISK before fresh confirmation generation.
Targeted tests:21passed. Confirmation contains108unique cells of1000histories
each, separate from18000reference histories and all V2/V3 streams.

Result: `FINITE_FAMILY_REFERENCE_ONLY`.
All18supported null cells pass the unchanged pointwise Wilson-upper7.5% criterion.
Seven false positives across18000null histories; this pooled count does not replace
the required cellwise checks. All36refusal cells refuse all1000histories each.

Critical limitation: at an additive0.5% effect,17of18model/length cells detect
0of1000histories. Volatility-shift180days detects12of1000. Size control was bought
with near-zero power at this effect, not a useful general market method.
Cutoffs90/180/365days:0.062331821910642425,0.036341832993420704,
0.035982765795621464. These are return units, about6.233%,3.634%,3.598%,
not basis points or annualized returns.

Artifacts: `research/research_corrections_20261009/cmc_calibration_v4_reference/`:
18reference receipts, immutable lock, hash-bound review acceptance,108confirmation
receipts and confirmation_summary_v4.json. The summary remains scoring-disabled.
Original failed V2/V3 studies and market artifacts are unchanged.

Conclusion: reference feasibility question answered; no defensible primary CMC
scorer established. Do not weaken cutoffs against this confirmation sample.
Any further method study needs a new explicit contract and fresh confirmation.
This result does not claim applicability beyond the finite synthetic family.
