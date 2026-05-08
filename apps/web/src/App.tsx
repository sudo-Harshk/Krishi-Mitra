import { useMemo, useState, type FormEvent } from "react";

type DiagnoseResponse = {
  summary_en: string;
  summary_te: string;
  likely_issue: string;
  action_steps_en: string[];
  action_steps_te: string[];
  weather_warning_en?: string | null;
  weather_warning_te?: string | null;
  confidence: number;
  source_notes: string[];
};

const initialResult: DiagnoseResponse = {
  summary_en: "No diagnosis yet.",
  summary_te: "ఇంకా నిర్ధారణ లేదు.",
  likely_issue: "N/A",
  action_steps_en: [],
  action_steps_te: [],
  confidence: 0,
  source_notes: []
};

export default function App() {
  const [cropName, setCropName] = useState("");
  const [problemDescription, setProblemDescription] = useState("");
  const [location, setLocation] = useState("");
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnoseResponse>(initialResult);

  const canSubmit = useMemo(
    () => cropName.trim().length > 0 && problemDescription.trim().length > 0,
    [cropName, problemDescription]
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!canSubmit) {
      setError("Crop name and problem description are required.");
      return;
    }

    setIsLoading(true);

    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
      const response = await fetch(`${apiBaseUrl}/diagnose`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            crop_name: cropName,
            problem_description: problemDescription,
            location: location || null,
            image_url: imagePreview
          })
        });

      if (!response.ok) {
        throw new Error("Failed to get diagnosis.");
      }

      const data = (await response.json()) as DiagnoseResponse;
      setResult(data);
    } catch {
      setError("Unable to reach the diagnosis service right now.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">Krishi Mitra</p>
        <h1>Clean crop advice web app</h1>
        <p className="lead">
          Upload a crop photo, describe the problem, and get bilingual guidance
          in a simple mobile-first layout.
        </p>
      </section>

      <section className="panel-grid">
        <form className="card form-card" onSubmit={handleSubmit}>
          <h2>Diagnosis input</h2>

          <label>
            Crop name
            <input
              value={cropName}
              onChange={(event) => setCropName(event.target.value)}
              placeholder="e.g. tomato"
              required
            />
          </label>

          <label>
            Problem description
            <textarea
              value={problemDescription}
              onChange={(event) => setProblemDescription(event.target.value)}
              placeholder="e.g. yellow spots on leaves, leaves curling"
              rows={5}
              required
            />
          </label>

          <label>
            Optional location
            <input
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              placeholder="e.g. Guntur"
            />
          </label>

          <label>
            Optional photo
            <input
              type="file"
              accept="image/*"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (!file) {
                  setImagePreview(null);
                  return;
                }
                setImagePreview(URL.createObjectURL(file));
              }}
            />
          </label>

          <button type="submit" disabled={!canSubmit || isLoading}>
            {isLoading ? "Checking..." : "Get advice"}
          </button>

          {error ? <p className="error">{error}</p> : null}
        </form>

        <aside className="card result-card">
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
          </div>
        </aside>
      </section>
    </main>
  );
}
