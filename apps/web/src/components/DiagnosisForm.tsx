import type { ChangeEvent, FormEvent } from "react";

type Props = {
  cropName: string;
  problemDescription: string;
  detectedLocation: string;
  locationStatus: string;
  isDetectingLocation: boolean;
  imagePreview: string | null;
  canSubmit: boolean;
  isLoading: boolean;
  error: string | null;
  onCropNameChange: (value: string) => void;
  onProblemDescriptionChange: (value: string) => void;
  onImageChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onDetectLocation: () => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function DiagnosisForm({
  cropName,
  problemDescription,
  detectedLocation,
  locationStatus,
  isDetectingLocation,
  imagePreview,
  canSubmit,
  isLoading,
  error,
  onCropNameChange,
  onProblemDescriptionChange,
  onImageChange,
  onDetectLocation,
  onSubmit
}: Props) {
  return (
    <form className="surface form-card" onSubmit={onSubmit}>
      <h2>Diagnosis input</h2>

      <label>
        Crop name
        <input
          value={cropName}
          onChange={(event) => onCropNameChange(event.target.value)}
          placeholder="e.g. tomato"
          required
        />
      </label>

      <label>
        Problem description
        <textarea
          value={problemDescription}
          onChange={(event) => onProblemDescriptionChange(event.target.value)}
          placeholder="e.g. yellow spots on leaves, leaves curling"
          rows={5}
          required
        />
      </label>

      <div className="location-pill" aria-live="polite">
        <span className="location-label">Location</span>
        <strong>{detectedLocation || "Not detected yet"}</strong>
        <span className="location-status">{locationStatus}</span>
      </div>

      <button
        type="button"
        className="secondary-button"
        onClick={onDetectLocation}
        disabled={isDetectingLocation}
      >
        {isDetectingLocation ? "Detecting location..." : "Detect exact location"}
      </button>

      <label>
        Optional photo
        <input type="file" accept="image/*" onChange={onImageChange} />
      </label>

      {imagePreview ? (
        <div className="preview">
          <img src={imagePreview} alt="Selected crop preview" />
        </div>
      ) : null}

      <button type="submit" disabled={!canSubmit || isLoading}>
        {isLoading ? "Checking..." : "Get advice"}
      </button>

      {error ? <p className="error">{error}</p> : null}
    </form>
  );
}
