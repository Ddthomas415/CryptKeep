import { FormEvent, useState } from "react";
import { api } from "../../services/api";
import type { ExplainResponse } from "../../types/contracts";


export default function ResearchPage() {
  const [asset, setAsset] = useState("SOL");
  const [question, setQuestion] = useState("Why is SOL moving?");
  const [result, setResult] = useState<ExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const data = await api.explain({ asset, question });
      setResult(data);
    } catch {
      setError("Unable to load explanation right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Research</h1>
        <p className="text-slate-400 mt-1">
          Ask market questions and inspect the evidence.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="rounded-2xl border border-slate-800 bg-slate-900 p-4 space-y-4"
      >
        <div>
          <label className="block text-sm text-slate-300 mb-2">Asset</label>
          <input
            value={asset}
            onChange={(e) => setAsset(e.target.value)}
            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm text-slate-300 mb-2">Question</label>
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full rounded-lg bg-slate-950 border border-slate-700 px-3 py-2"
          />
        </div>

        <button
          type="submit"
          className="rounded-lg bg-slate-200 text-slate-950 px-4 py-2 font-medium"
          disabled={loading}
        >
          {loading ? "Running..." : "Explain"}
        </button>
      </form>

      {error && <div className="text-rose-400">{error}</div>}

      {result && (
        <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 space-y-4">
            <h2 className="text-lg font-medium">Answer</h2>

            <div>
              <div className="text-sm text-slate-400">Current Cause</div>
              <p className="mt-1">{result.current_cause}</p>
            </div>

            <div>
              <div className="text-sm text-slate-400">Past Precedent</div>
              <p className="mt-1">{result.past_precedent}</p>
            </div>

            <div>
              <div className="text-sm text-slate-400">Future Catalyst</div>
              <p className="mt-1">{result.future_catalyst}</p>
            </div>

            <div className="flex gap-6 text-sm">
              <div>Confidence: {result.confidence}</div>
              <div>{result.risk_note}</div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="text-lg font-medium mb-4">Evidence</h2>
            <div className="space-y-3">
              {result.evidence.map((item) => (
                <div
                  key={item.id}
                  className="rounded-xl border border-slate-800 bg-slate-950 p-3"
                >
                  <div className="text-sm text-slate-400">
                    {item.type} · {item.source}
                  </div>
                  <div className="mt-2">{item.summary}</div>
                  {item.timestamp && (
                    <div className="mt-2 text-xs text-slate-500">
                      {item.timestamp}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
