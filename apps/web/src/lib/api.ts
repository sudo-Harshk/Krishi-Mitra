import type { DiagnoseResponse } from "./types";

export async function diagnoseCrop(
  payload: FormData
): Promise<DiagnoseResponse> {
  const apiBaseUrl =
    import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ??
    "http://localhost:8000";

  const response = await fetch(`${apiBaseUrl}/diagnose`, {
    method: "POST",
    body: payload
  });

  if (!response.ok) {
    throw new Error("Failed to get diagnosis.");
  }

  return (await response.json()) as DiagnoseResponse;
}

