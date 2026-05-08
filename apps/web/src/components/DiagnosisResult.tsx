import type { DiagnoseResponse } from "../lib/types";

type Props = {
  result: DiagnoseResponse;
};

export function DiagnosisResult({ result }: Props) {
  return (
    <aside className="surface result-card">
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
    </aside>
  );
}

