import type { ChangeEvent, FormEvent } from "react";

type Props = {
  cropName: string;
  problemDescription: string;
  location: string;
  imagePreview: string | null;
  canSubmit: boolean;
  isLoading: boolean;
  error: string | null;
  onCropNameChange: (value: string) => void;
  onProblemDescriptionChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  onImageChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export function DiagnosisForm({
  cropName,
  problemDescription,
  location,
  imagePreview,
  canSubmit,
  isLoading,
  error,
  onCropNameChange,
  onProblemDescriptionChange,
  onLocationChange,
  onImageChange,
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

      <label>
        Optional location
        <input
          value={location}
          onChange={(event) => onLocationChange(event.target.value)}
          placeholder="e.g. Guntur"
        />
      </label>

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

