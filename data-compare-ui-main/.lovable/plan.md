

# Data Validation App — Payroll File Comparison Tool

## Design Direction
- **Palette**: Deep Blue (#0f172a, #1e3a5f) with Cyan (#06b6d4) accents on light backgrounds (#e0f2fe, white)
- **Style**: Premium, polished with smooth animations, glass-morphism cards, and subtle gradients — inspired by modern AI tools like Gimme AI
- **Typography**: Clean Inter/system font, generous spacing

## Pages & Flow

### 1. Upload Page (Home)
- Hero section with app branding and tagline ("Validate your payroll data in seconds")
- **Two-tab file upload area** — Tab 1: "Legacy/Paycor File", Tab 2: "ADP File"
- Each tab has a drag-and-drop zone with file type validation (.xlsx)
- File preview showing filename, size, and a remove button after upload
- "Start Validation" button (enabled only when both files uploaded)
- Connects to the user's existing API endpoint (placeholder URL, easily configurable)

### 2. Processing View
- Animated step-by-step progress indicator showing pipeline stages:
  1. Loading Files → 2. Detecting Headers → 3. Normalizing Data → 4. AI Column Mapping → 5. Matching Employees → 6. Comparing Fields → 7. Generating Report
- Each step shows status (pending / in-progress / complete) with smooth transitions
- Subtle loading animations and progress percentage

### 3. Results Dashboard
- **Summary cards** at top: Total Employees, Matched, Mismatched, Missing in ADP, Missing in Legacy
- **Donut/pie chart** showing match vs mismatch distribution
- Quick stats with animated counters

### 4. Detailed Results (Tabs)
- **Validation Sheet tab**: Full table of matched employees with field-by-field status (MATCH/MISMATCH/ERROR/BLANK), filterable and sortable
- **Discrepancies tab**: Only mismatched records with highlighted differences
- **Missing in ADP tab**: Employees found only in legacy system
- **Missing in Legacy tab**: Employees found only in ADP
- Each table supports search, column sorting, and export
- Download button for the final result.xlsx

## Technical Approach
- React SPA with React Router (upload → processing → results)
- API service layer with configurable endpoint URL
- Mock data mode