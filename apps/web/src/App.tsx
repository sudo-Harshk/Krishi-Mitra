import { useEffect, useMemo, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { DiagnosisForm } from "./components/DiagnosisForm";
import { DiagnosisResult } from "./components/DiagnosisResult";
import { Hero } from "./components/Hero";
import { diagnoseCrop } from "./lib/api";
import type { DiagnoseResponse } from "./lib/types";

async function compressImage(file: File, maxDimension = 1024, quality = 0.82): Promise<File> {
  return new Promise((resolve) => {
    const img = new Image();
    const objectUrl = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      const { width, height } = img;
      const scale = Math.min(1, maxDimension / Math.max(width, height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
      const ctx = canvas.getContext("2d");
      if (!ctx) { resolve(file); return; }
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(
        (blob) => {
          if (!blob) { resolve(file); return; }
          resolve(new File([blob], file.name.replace(/\.[^.]+$/, ".jpg"), { type: "image/jpeg" }));
        },
        "image/jpeg",
        quality
      );
    };
    img.onerror = () => { URL.revokeObjectURL(objectUrl); resolve(file); };
    img.src = objectUrl;
  });
}

export default function App() {
  const [cropName, setCropName] = useState("");
  const [problemDescription, setProblemDescription] = useState("");
  const [detectedLocation, setDetectedLocation] = useState("");
  const [locationStatus, setLocationStatus] = useState("Tap to detect your location");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DiagnoseResponse | null>(null);
  const resultRef = useRef<HTMLElement>(null);

  async function resolveLocation(latitude?: number, longitude?: number) {
    const params = new URLSearchParams({ localityLanguage: "en" });
    if (typeof latitude === "number" && typeof longitude === "number") {
      params.set("latitude", String(latitude));
      params.set("longitude", String(longitude));
    }

    const response = await fetch(
      `https://api.bigdatacloud.net/data/reverse-geocode-client?${params.toString()}`
    );
    if (!response.ok) {
      throw new Error("Location lookup failed");
    }

    const data = (await response.json()) as {
      city?: string;
      locality?: string;
      principalSubdivision?: string;
      countryName?: string;
      lookupSource?: string;
    };

    const parts = [data.city, data.locality, data.principalSubdivision].filter(Boolean);
    const resolved = parts.length > 0 ? parts.join(", ") : data.countryName || "";
    return {
      label: resolved,
      source: data.lookupSource === "coordinates" ? "GPS" : "IP fallback",
    };
  }

  async function handleDetectLocation() {
    setIsDetectingLocation(true);
    setLocationStatus("Detecting your location...");

    try {
      if (!navigator.geolocation) {
        const fallback = await resolveLocation();
        setDetectedLocation(fallback.label);
        setLocationStatus(`Resolved via ${fallback.source}`);
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const result = await resolveLocation(
              position.coords.latitude,
              position.coords.longitude
            );
            setDetectedLocation(result.label);
            setLocationStatus(`Resolved via ${result.source}`);
          } catch {
            const fallback = await resolveLocation();
            setDetectedLocation(fallback.label);
            setLocationStatus(`Resolved via ${fallback.source}`);
          } finally {
            setIsDetectingLocation(false);
          }
        },
        async () => {
          try {
            const fallback = await resolveLocation();
            setDetectedLocation(fallback.label);
            setLocationStatus(`Resolved via ${fallback.source}`);
          } catch {
            setDetectedLocation("");
            setLocationStatus("Location unavailable");
          } finally {
            setIsDetectingLocation(false);
          }
        },
        { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
      );
    } catch {
      setDetectedLocation("");
      setLocationStatus("Location unavailable");
      setIsDetectingLocation(false);
    }
  }

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
      if (detectedLocation.trim()) {
        formData.append("location", detectedLocation.trim());
      }
      if (imageFile) {
        const compressed = await compressImage(imageFile);
        formData.append("image_file", compressed);
      }

      const data = await diagnoseCrop(formData);
      setResult(data);
      // On mobile the panels stack — scroll the result into view
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
    } catch {
      setError("Unable to reach the diagnosis service right now.");
    } finally {
      setIsLoading(false);
    }
  }

  function handleReset() {
    setCropName("");
    setProblemDescription("");
    setDetectedLocation("");
    setLocationStatus("Tap to detect your location");
    setImageFile(null);
    setImagePreview(null);
    setError(null);
    setResult(null);
  }

  function handleImageChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;

    if (!file) {
      setImageFile(null);
      setImagePreview(null);
      return;
    }

    if (!file.type.startsWith("image/")) {
      setError("Only image files are supported.");
      event.target.value = "";
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("Image must be under 10 MB.");
      event.target.value = "";
      return;
    }

    setError(null);
    setImageFile(file);
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
          detectedLocation={detectedLocation}
          locationStatus={locationStatus}
          isDetectingLocation={isDetectingLocation}
          imagePreview={imagePreview}
          canSubmit={canSubmit}
          isLoading={isLoading}
          error={error}
          onCropNameChange={setCropName}
          onProblemDescriptionChange={setProblemDescription}
          onImageChange={handleImageChange}
          onDetectLocation={handleDetectLocation}
          onSubmit={handleSubmit}
        />

        <DiagnosisResult ref={resultRef} result={result} isLoading={isLoading} onReset={handleReset} />
      </section>
    </main>
  );
}
