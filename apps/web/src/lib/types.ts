export type DiagnoseResponse = {
  summary_en: string;
  summary_te: string;
  likely_issue: string;
  action_steps_en: string[];
  action_steps_te: string[];
  weather_warning_en?: string | null;
  weather_warning_te?: string | null;
  confidence: number;
  source_notes: string[];
  image_received?: boolean;
};

export type DiagnosisFormState = {
  cropName: string;
  problemDescription: string;
  location: string;
  imageFile: File | null;
};

