import { FormEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ConfidenceBadge } from "../components/badges/ConfidenceBadge";
import { TimelineBadge } from "../components/badges/TimelineBadge";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState } from "../components/states/EmptyState";
import { ErrorState } from "../components/states/ErrorState";
import { LoadingState } from "../components/states/LoadingState";
import { mockApi } from "../services/mockApi";
import { useAppUI } from "../state/AppUIContext";
import type { ExplainResponse, ResearchFiltersValue, ResearchHistoryItem, Timeline } from "../types/contracts";

const defaultFilters: ResearchFiltersValue = {
  asset: "SOL",
  exchange: "coinbase",
  source_types: ["market", "news", "archive", "future_event"],
  timelines: ["past", "present", "future"],
  time_range: "24h",
  confidence_min: 0.5,
  include_archives: true,
  include_onchain: true,
  include_social: false
};

export function ResearchPage() {
  const { setEvidencePanel } = useAppUI();
  const [searchParams] = useSearchParams();
  const [question, setQuestion] = useState(searchParams.get("q") || "Why is SOL moving?");
  const [filters, setFilters] = useState<ResearchFiltersValue>(defaultFilters);
  const [answer, setAnswer] = useState<ExplainResponse | null>(null);
  const [history, setHistory] = useState<ResearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const timelineLabel = useMemo(() => filters.timelines.join(", "), [filters.timelines]);

  useEffect(() => {
    void mockApi.getResearchHistory().then(setHistory);
  }, []);

  useEffect(() => {
    if (answer) {
      setEvidencePanel("Research Evidence", answer.evidence);
    }
  }, [answer, setEvidencePanel]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const out = await mockApi.postResearchExplain({ question, asset: filters.asset, filters });
      setAnswer(out);
      const refreshed = await mockApi.getResearchHistory();
      setHistory(refreshed);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const toggleTimeline = (value: Timeline) => {
    setFilters((prev) => {
      const exists = prev.timelines.includes(value);
      const timelines = exists ? prev.timelines.filter((item) => item !== value) : [...prev.timelines, value];
      return { ...prev, timelines: timelines.length ? timelines : ["present"] };
    });
  };

  return (
    <section>
      <PageHeader title="Research" subtitle="Ask questions with past/present/future evidence and confidence scoring." />

      <form className="card card-wide" onSubmit={onSubmit}>
        <div className="form-grid">
          <label>
            Ask
            <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Why is SOL moving?" />
          </label>
          <label>
            Asset
            <input value={filters.asset ?? ""} onChange={(event) => setFilters((prev) => ({ ...prev, asset: event.target.value }))} />
          </label>
          <label>
            Exchange
            <input value={filters.exchange ?? ""} onChange={(event) => setFilters((prev) => ({ ...prev, exchange: event.target.value }))} />
          </label>
          <label>
            Time range
            <select value={filters.time_range} onChange={(event) => setFilters((prev) => ({ ...prev, time_range: event.target.value }))}>
              <option value="1h">1h</option>
              <option value="24h">24h</option>
              <option value="7d">7d</option>
              <option value="90d">90d</option>
            </select>
          </label>
          <label>
            Confidence threshold
            <input
              type="number"
              min={0}
              max={1}
              step={0.05}
              value={filters.confidence_min}
              onChange={(event) => setFilters((prev) => ({ ...prev, confidence_min: Number(event.target.value) }))}
            />
          </label>
        </div>

        <div className="row-inline wrap">
          <span>Timeline:</span>
          {(["past", "present", "future"] as Timeline[]).map((item) => (
            <button key={item} type="button" onClick={() => toggleTimeline(item)}>
              <TimelineBadge timeline={item} />
            </button>
          ))}
          <span className="hint">Active: {timelineLabel}</span>
        </div>

        <div className="row-inline wrap">
          <label className="check-row">
            <input
              type="checkbox"
              checked={filters.include_archives}
              onChange={(event) => setFilters((prev) => ({ ...prev, include_archives: event.target.checked }))}
            />
            <span>Include archives</span>
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={filters.include_onchain}
              onChange={(event) => setFilters((prev) => ({ ...prev, include_onchain: event.target.checked }))}
            />
            <span>Include on-chain</span>
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={filters.include_social}
              onChange={(event) => setFilters((prev) => ({ ...prev, include_social: event.target.checked }))}
            />
            <span>Include social</span>
          </label>
          <button type="submit">Run Query</button>
        </div>
      </form>

      {loading ? <LoadingState label="Running explanation..." /> : null}
      {error ? <ErrorState message={error} /> : null}

      {!loading && !answer ? (
        <EmptyState title="No query yet" description="Ask a market question to populate current, past, and future context." />
      ) : null}

      {answer ? (
        <div className="card-grid">
          <article className="card">
            <h2>Current Cause</h2>
            <p>{answer.current_cause}</p>
          </article>
          <article className="card">
            <h2>Past Precedent</h2>
            <p>{answer.past_precedent}</p>
          </article>
          <article className="card">
            <h2>Future Catalyst</h2>
            <p>{answer.future_catalyst}</p>
          </article>
          <article className="card">
            <h2>Confidence and Risk</h2>
            <ConfidenceBadge score={answer.confidence} />
            <p>{answer.risk_note}</p>
            <p>Execution disabled: {String(answer.execution_disabled)}</p>
          </article>
          <article className="card card-wide">
            <h2>Evidence</h2>
            {answer.evidence.map((item) => (
              <div className="row" key={item.id}>
                <span>{item.source}</span>
                <span>{item.type}</span>
                <span>{item.summary}</span>
                <span>{item.timestamp}</span>
              </div>
            ))}
          </article>
        </div>
      ) : null}

      <article className="card card-wide">
        <h2>Research History</h2>
        {!history.length ? <EmptyState title="No history" description="Your prior questions will appear here." /> : null}
        {history.map((item) => (
          <div className="row" key={item.id}>
            <span>{item.timestamp}</span>
            <span>{item.asset}</span>
            <span>{item.question}</span>
            <ConfidenceBadge score={item.confidence} />
          </div>
        ))}
      </article>
    </section>
  );
}
