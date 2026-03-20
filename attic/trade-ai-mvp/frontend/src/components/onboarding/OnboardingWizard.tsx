import { useMemo, useState } from "react";
import type { Mode, OnboardingState } from "../../types/contracts";

const steps = ["Mode", "Sources", "Watchlist", "Risk", "First Query"];

const modeOptions: Mode[] = ["research_only", "paper", "live_approval"];
const riskProfiles: OnboardingState["risk_profile"][] = ["conservative", "balanced", "advanced"];
const interestOptions = ["BTC", "ETH", "SOL", "DeFi", "AI tokens", "memecoins"];

export function OnboardingWizard({
  open,
  onClose,
  onComplete
}: {
  open: boolean;
  onClose: () => void;
  onComplete: (state: OnboardingState) => void;
}) {
  const [stepIndex, setStepIndex] = useState(0);
  const [state, setState] = useState<OnboardingState>({
    mode: "research_only",
    exchange: "coinbase",
    risk_profile: "conservative",
    interests: ["BTC", "ETH", "SOL"],
    completed: false
  });

  const lastStep = stepIndex === steps.length - 1;
  const progress = useMemo(() => `${stepIndex + 1}/${steps.length}`, [stepIndex]);

  if (!open) return null;

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="modal" role="dialog" aria-modal="true" aria-label="Onboarding wizard">
        <h3>Onboarding Wizard</h3>
        <p className="hint">
          Step {progress}: {steps[stepIndex]}
        </p>

        {stepIndex === 0 ? (
          <div className="row-inline wrap">
            {modeOptions.map((mode) => (
              <button key={mode} type="button" onClick={() => setState((prev) => ({ ...prev, mode }))}>
                {mode}
              </button>
            ))}
          </div>
        ) : null}

        {stepIndex === 1 ? (
          <label>
            Exchange
            <select value={state.exchange} onChange={(event) => setState((prev) => ({ ...prev, exchange: event.target.value }))}>
              <option value="coinbase">Coinbase</option>
              <option value="binance">Binance</option>
              <option value="kraken">Kraken</option>
              <option value="okx">OKX</option>
            </select>
          </label>
        ) : null}

        {stepIndex === 2 ? (
          <div className="form-grid">
            {interestOptions.map((item) => {
              const checked = state.interests.includes(item);
              return (
                <label className="check-row" key={item}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={(event) => {
                      setState((prev) => {
                        if (event.target.checked) return { ...prev, interests: [...prev.interests, item] };
                        return { ...prev, interests: prev.interests.filter((existing) => existing !== item) };
                      });
                    }}
                  />
                  <span>{item}</span>
                </label>
              );
            })}
          </div>
        ) : null}

        {stepIndex === 3 ? (
          <div className="row-inline wrap">
            {riskProfiles.map((profile) => (
              <button key={profile} type="button" onClick={() => setState((prev) => ({ ...prev, risk_profile: profile }))}>
                {profile}
              </button>
            ))}
          </div>
        ) : null}

        {stepIndex === 4 ? <p>Suggested first question: Why is BTC moving?</p> : null}

        <div className="modal-actions">
          <button type="button" onClick={onClose}>
            Cancel
          </button>
          <button type="button" onClick={() => setStepIndex((prev) => Math.max(prev - 1, 0))} disabled={stepIndex === 0}>
            Back
          </button>
          {!lastStep ? (
            <button type="button" onClick={() => setStepIndex((prev) => Math.min(prev + 1, steps.length - 1))}>
              Next
            </button>
          ) : (
            <button
              type="button"
              className="danger-btn"
              onClick={() => {
                const completed = { ...state, completed: true };
                onComplete(completed);
                onClose();
              }}
            >
              Start Dashboard
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
