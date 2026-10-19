# Statistical v3 confirmation: negative result

Role: ENGINEER. Status: READY_FOR_INDEPENDENT_REVIEW for artifact aggregation.
Result: `NO_CERTIFIED_SAMPLE_V3`.

The locked studentized circular-block14 method completed the exact 108-cell grid, 1000 histories per cell (108000 total), in approximately 24.4 seconds. Original development/legacy artifacts are preserved; results are under `research/research_corrections_20261009/cmc_calibration_v3_evidence_v2/`.

All supported null histories were available. Only iid at 90/180/365 days passed the registered pointwise Wilson-95% upper false-positive tolerance of 7.5%. All 15 dependent/heavy-tail/unequal/volatility-shift null cells failed. At 365 days false-positive counts per 1000 were iid52, overlap63, persistent86, heavy-tail69, shared-unequal60 and volatility-shift97. All refusal-only cells refused every history as required.

Power is descriptive, not a certification requirement under the operator's size-only decision. At mean0.005 and365 days, positive rates were iid93.4%, overlap37.4%, persistent35.9%, heavy-tail38.8%, shared-unequal37.3% and volatility-shift18.2%. These do not establish power for actual market returns.

Consequence: primary CMC scoring remains disabled. This method is not certified under the approved scenario grid. Do not retune it on these confirmation outcomes or run another candidate under the same confirmation seeds. Any new method study requires a separately approved contract and fresh confirmation identity. Descriptive forward-data collection can continue; this is a statistical-method failure, not evidence that trending is profitable or unprofitable.

Independent artifact/grid/aggregation review requested without rerunning histories.
