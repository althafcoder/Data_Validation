// Dynamically use the hostname of the machine serving the frontend, 
// so it works from other machines on the network (e.g., 10.10.8.x)
const API_BASE_URL = `http://${window.location.hostname}:8000/api`;

export interface ValidationRequest {
  legacyFile: File;
  adpFile: File;
}

export interface PipelineStep {
  id: number;
  label: string;
  status: "pending" | "in-progress" | "complete" | "error";
}

export interface SummaryData {
  totalEmployees: number;
  matched: number;
  mismatched: number;
  missingInADP: number;
  missingInLegacy: number;
}

export type CellStatus = "MATCH" | "MISMATCH" | "ERROR" | "BLANK";

export interface ValidationRow {
  id: string;
  employeeName: string;
  employeeId: string;
  fields: Record<string, { legacy: string; adp: string; status: CellStatus }>;
}

export interface DiscrepancyRow {
  id: string;
  employeeName: string;
  employeeId: string;
  field: string;
  legacyValue: string;
  adpValue: string;
}

export interface MissingEmployee {
  id: string;
  employeeName: string;
  employeeId: string;
  source: "legacy" | "adp";
}

export interface ValidationResult {
  sessionId: string;
  jobSessionId?: string;
  taxSessionId?: string;
  complianceSessionId?: string;
  summary: SummaryData;
  validationSheet: ValidationRow[];
  discrepancies: DiscrepancyRow[];
  missingInADP: MissingEmployee[];
  missingInLegacy: MissingEmployee[];
}

export const PIPELINE_STEPS: PipelineStep[] = [
  { id: 1, label: "Loading Files", status: "pending" },
  { id: 2, label: "Detecting Headers", status: "pending" },
  { id: 3, label: "Normalizing Data", status: "pending" },
  { id: 4, label: "AI Column Mapping", status: "pending" },
  { id: 5, label: "Matching Employees", status: "pending" },
  { id: 6, label: "Comparing Fields", status: "pending" },
  { id: 7, label: "Generating Report", status: "pending" },
];

export async function submitValidation(request: ValidationRequest, fieldGroup: "personal" | "job" | "tax" | "compliance" = "personal"): Promise<ValidationResult> {
  const formData = new FormData();
  formData.append("legacyFile", request.legacyFile);
  formData.append("adpFile", request.adpFile);

  const response = await fetch(`${API_BASE_URL}/validate?fieldGroup=${fieldGroup}`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorMessage = response.statusText;
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch (e) {
      // Ignore if not JSON
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

export function exportValidationResult(sessionId: string, jobSessionId?: string, taxSessionId?: string, complianceSessionId?: string) {
  const downloadUrl = (url: string) => {
    const a = document.createElement("a");
    a.href = url;
    a.download = "";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };
  
  if (jobSessionId) {
    let url = `${API_BASE_URL}/export-zip?personal_id=${sessionId}&job_id=${jobSessionId}`;
    if (taxSessionId) {
      url += `&tax_id=${taxSessionId}`;
    }
    if (complianceSessionId) {
      url += `&compliance_id=${complianceSessionId}`;
    }
    downloadUrl(url);
  } else {
    downloadUrl(`${API_BASE_URL}/export/${sessionId}`);
  }
}
