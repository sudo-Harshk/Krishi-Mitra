import { forwardRef } from "react";
import type { DiagnoseResponse } from "../lib/types";

type Props = {
  result: DiagnoseResponse | null;
  isLoading: boolean;
  onReset: () => void;
};

export const DiagnosisResult = forwardRef<HTMLElement, Props>(function DiagnosisResult(
  { result, isLoading, onReset },
  ref
) {
  if (isLoading) {
    return (
      <aside ref={ref} className="surface result-card">
        <h2 className="skeleton-heading">Analysing your crop...</h2>
        <div className="skeleton-block" />
        <div className="skeleton-block skeleton-narrow" />
        <div className="skeleton-list">
          <div className="skeleton-line" />
          <div className="skeleton-line skeleton-narrow" />
          <div className="skeleton-line" style={{ width: "45%" }} />
        </div>
        <div className="skeleton-block" />
        <div className="skeleton-block skeleton-narrow" />
      </aside>
    );
  }

  if (!result) {
    return (
      <aside ref={ref} className="surface result-card result-empty">
        <p className="result-empty-icon">🌱</p>
        <p className="result-empty-title">Your diagnosis will appear here</p>
        <p className="muted">
          Fill in the crop name and problem description, then tap <strong>Get advice</strong>.
        </p>
      </aside>
    );
  }

  return (
    <aside ref={ref} className="surface result-card">
      <h2>Result</h2>

      <div className="result-block">
        <p className="result-label">English</p>
        <p>{result.summary_en}</p>
        <p className="muted">Likely issue: {result.likely_issue}</p>
        <ul>
          {result.action_steps_en.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
        {result.weather_warning_en ? (
          <p className="warning">{result.weather_warning_en}</p>
        ) : null}
      </div>

      <div className="result-block">
        <p className="result-label">Telugu</p>
        <p>{result.summary_te}</p>
        <ul>
          {result.action_steps_te.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
        {result.weather_warning_te ? (
          <p className="warning">{result.weather_warning_te}</p>
        ) : null}
      </div>

      <div className="meta-row">
        <span>Confidence: {Math.round(result.confidence * 100)}%</span>
        {typeof result.image_received === "boolean" ? (
          <span>{result.image_received ? "Image received" : "No image"}</span>
        ) : null}
      </div>

      <button type="button" className="secondary-button" onClick={onReset}>
        New diagnosis
      </button>
    </aside>
  );
});
