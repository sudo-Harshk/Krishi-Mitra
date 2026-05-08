import { useEffect, useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import { DiagnosisForm } from "./components/DiagnosisForm";
import { DiagnosisResult } from "./components/DiagnosisResult";
import { Hero } from "./components/Hero";
import { diagnoseCrop } from "./lib/api";
import type { DiagnoseResponse } from "./lib/types";

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
  const [imageFile, setImageFile] = useState<File | null>(null);
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
      const formData = new FormData();
      formData.append("crop_name", cropName.trim());
      formData.append("problem_description", problemDescription.trim());
      if (location.trim()) {
        formData.append("location", location.trim());
      }
      if (imageFile) {
        formData.append("image_file", imageFile);
      }

      const data = await diagnoseCrop(formData);
      setResult(data);
    } catch {
      setError("Unable to reach the diagnosis service right now.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    setImageFile(file);

    if (!file) {
      setImagePreview(null);
      return;
    }

    setImagePreview(URL.createObjectURL(file));
  }

  useEffect(() => {
    return () => {
      if (imagePreview) {
        URL.revokeObjectURL(imagePreview);
      }
    };
  }, [imagePreview]);

  return (
    <main className="app-shell">
      <Hero />

      <section className="panel-grid">
        <DiagnosisForm
          cropName={cropName}
          problemDescription={problemDescription}
          location={location}
          imagePreview={imagePreview}
          canSubmit={canSubmit}
          isLoading={isLoading}
          error={error}
          onCropNameChange={setCropName}
          onProblemDescriptionChange={setProblemDescription}
          onLocationChange={setLocation}
          onImageChange={handleImageChange}
          onSubmit={handleSubmit}
        />

        <DiagnosisResult result={result} />
      </section>
    </main>
  );
}
