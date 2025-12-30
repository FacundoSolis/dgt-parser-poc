# DGT Parser POC

Parser de informes DGT para empresa energética Barcelona.

# DGT Parser POC

DGT vehicle report parser (Dirección General de Tráfico) for vehicle processing.

Developed for an energy company in Barcelona — processes "Informe del Vehículo" reports and applies complex business rules.

## Features

- ✅ Deterministic extraction (no LLM hallucinations)
- ✅ Text parsing with regex optimized for Spanish PDFs
- ✅ Complete business rules (ownership, renting, deregistrations, ITV filtering)
- ✅ CSV output with exact required columns

## Installation
```bash
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

## Usage
```bash
# 1. Copy PDFs to process
cp /path/to/pdfs/*.pdf data/pdfs/

# 2. Run processing
python src/main.py

# 3. View results
cat data/output/resultados.csv
# Or open with Excel/LibreOffice
```

## Project Structure
```
dgt-parser-poc/
├── data/
│   ├── pdfs/          # Input PDFs (DGT reports)
│   └── output/        # Output CSV
├── src/
│   ├── __init__.py
│   ├── pdf_parser.py       # Data extraction from PDFs
│   ├── business_logic.py   # Business rules
│   └── main.py             # Main script
├── requirements.txt
└── README.md
```

## Output Format

CSV table with exact columns:

| Column | Description |
|--------|-------------|
| License plate | Vehicle registration number |
| Penultimate date | Penultimate valid ITV date |
| Penultimate reading (km) | Odometer at penultimate ITV |
| Last date | Last valid ITV date |
| Last reading (km) | Odometer at last ITV |
| Days between | Days between last and penultimate ITV |
| km ITVs | Kilometers difference between ITVs |
| km 1 year | Annualized kilometers (projected over 365 days) |
| km int | International kilometers (N/A) |
| km nac | National kilometers (N/A) |
| Comments | Validation messages / warnings |

## Implemented Business Rules

### 1. Ownership Validation
- Checks whether the current owner matches the authorized client
- If it does not match, proceeds to renting verification

### 2. Renting Validation
- If `Renting = Yes`: verifies current lessee
- If current lessee does not match: searches historical periods > 14 months
- If `Renting = No`: searches owner history > 14 months

### 3. Deregistration Detection
- Searches for deregistrations **after 01/01/2023**
- Adds a comment: "Vehicle deregistered from [date] to [date]"

### 4. ITV Selection and Calculations
**Applied filters:**
- ❌ Exclude ITVs with result DESFAVORABLE or NEGATIVE
- ❌ Exclude ITVs with decreasing odometer readings
- ✅ Prioritize ITVs with odometer readings > 0
- ✅ Keep chronological order

**Calculations:**
- `Days between = Last date - Penultimate date`
- `km ITVs = Last reading - Penultimate reading`
- `km 1 year = (km ITVs × 365) / Days between`

## Data Extracted per PDF

**Identification:**
- License plate, VIN, Make, Model
- Vehicle type, Service
- Maximum mass, Unladen weight

**Owner:**
- Current owner information
- Co-owners

**Renting:**
- Status (Yes/No)
- Current lessee
- Lessee history

**Histories:**
- Owners (start/end dates, type)
- Technical inspections (ITV): date, result, km, defects
- Temporary / permanent deregistrations

## Use Cases / Comments

The system generates automatic comments for special cases:

- "Only one valid ITV available" → New vehicle or no full history
- "Only one ITV with odometer reading available" → First ITV missing km
- "Valid ITVs without odometer readings" → ITVs without odometer values
- "No valid ITVs (all DESFAVORABLE/NEGATIVE)" → All failed inspections
- "The vehicle is not eligible to generate CAEs" → Ownership/renting criteria not met
- "Vehicle deregistered from DD/MM/YYYY to DD/MM/YYYY" → Deregistration after 2023

## Test PDFs Processed

| Plate | Vehicle | ITVs | Notes |
|------:|---------|----:|-------|
| 0155MXR | Peugeot 208 | 1 | No km |
| 1022LKX | Mercedes Sprinter | 6 | Complete ✓ |
| 2860LZG | Iveco 70C18 | 4 | Renting ✓ |
| 3191MGK | Peugeot Van | 2 | Only 1 with km |
| 5442MFB | Citroën Van | 2 | Only 1 with km |
| 7878MBG | Iveco 35C14 | 2 | Renting |
| 9952HPL | Irisbus Xerus | 10 | Deregistration (COVID) |
| 9990JJY | Volvo NCENTURY | 13 | Deregistration (COVID) |

## Technologies

- **Python 3.8+**
- **pdfplumber**: Text and table extraction from PDFs
- **pandas**: Data manipulation
- **python-dateutil**: Spanish date parsing

## Client Mode (Optional)

To enable filtering by a specific client, edit `src/main.py`:
```python
# No filter mode (process all)
cliente_nif = None

# Client filter mode
cliente_nif = "COMPANY NAME SL"
```

## Technical Notes

- PDFs processed: DGT "INFORME DEL VEHÍCULO" format
- Dates: Spanish format DD/MM/YYYY
- Encoding: UTF-8
- CSV separator: comma (,)
- Deregistrations before 01/01/2023 are ignored (e.g., COVID 2020 deregistrations)

## Contact

POC project for Travis Dayton
Developer: Facundo Ezequiel Solis

2860LZG: Iveco 70C18 (4 ITVs, leasing)

3191MGK: Peugeot van (2 ITVs, leasing)

5442MFB: Citroën van (2 ITVs, leasing)

7878MBG: Iveco 35C14 (2 ITVs, leasing)

9952HPL: Irisbus Xerus (10 ITVs, 1 deregistration)

9990JJY: Volvo NCENTURY (13 ITVs, 1 deregistration)