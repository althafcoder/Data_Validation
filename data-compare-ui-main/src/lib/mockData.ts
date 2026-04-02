import type { ValidationResult, ValidationRow, DiscrepancyRow, MissingEmployee, CellStatus } from "./api";

const fields = ["Pay Rate", "Hours", "Gross Pay", "Federal Tax", "State Tax", "Net Pay", "401k", "Health Insurance"];

function randomStatus(): CellStatus {
  const r = Math.random();
  if (r < 0.6) return "MATCH";
  if (r < 0.85) return "MISMATCH";
  if (r < 0.95) return "ERROR";
  return "BLANK";
}

const employees = [
  "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "David Kim", "Jessica Williams",
  "James Brown", "Amanda Taylor", "Robert Davis", "Lisa Anderson", "Christopher Wilson",
  "Maria Garcia", "Daniel Martinez", "Jennifer Lopez", "Kevin Thomas", "Ashley Moore",
  "Brian Jackson", "Stephanie White", "Matthew Harris", "Nicole Martin", "Andrew Thompson",
  "Michelle Lee", "Joshua Robinson", "Samantha Clark", "Ryan Lewis", "Rebecca Walker",
];

function generateValidationSheet(): ValidationRow[] {
  return employees.slice(0, 20).map((name, i) => {
    const fieldData: ValidationRow["fields"] = {};
    fields.forEach((f) => {
      const status = randomStatus();
      const val = (Math.random() * 5000 + 1000).toFixed(2);
      fieldData[f] = {
        legacy: `$${val}`,
        adp: status === "MATCH" ? `$${val}` : `$${(Math.random() * 5000 + 1000).toFixed(2)}`,
        status,
      };
    });
    return { id: `EMP-${1000 + i}`, employeeName: name, employeeId: `EMP-${1000 + i}`, fields: fieldData };
  });
}

function generateDiscrepancies(sheet: ValidationRow[]): DiscrepancyRow[] {
  const rows: DiscrepancyRow[] = [];
  sheet.forEach((row) => {
    Object.entries(row.fields).forEach(([field, data]) => {
      if (data.status === "MISMATCH") {
        rows.push({
          id: `${row.id}-${field}`,
          employeeName: row.employeeName,
          employeeId: row.employeeId,
          field,
          legacyValue: data.legacy,
          adpValue: data.adp,
        });
      }
    });
  });
  return rows;
}

function generateMissing(source: "legacy" | "adp"): MissingEmployee[] {
  const start = source === "adp" ? 20 : 22;
  return employees.slice(start, start + 3).map((name, i) => ({
    id: `MISS-${source}-${i}`,
    employeeName: name,
    employeeId: `EMP-${2000 + i}`,
    source,
  }));
}

export function generateMockResult(): ValidationResult {
  const sheet = generateValidationSheet();
  const discrepancies = generateDiscrepancies(sheet);
  const missingInADP = generateMissing("adp");
  const missingInLegacy = generateMissing("legacy");

  return {
    summary: {
      totalEmployees: 25,
      matched: 15,
      mismatched: 5,
      missingInADP: missingInADP.length,
      missingInLegacy: missingInLegacy.length,
    },
    validationSheet: sheet,
    discrepancies,
    missingInADP,
    missingInLegacy,
  };
}
