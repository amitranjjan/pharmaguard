# 💊 PharmaGuard — Pharmacogenomic Risk Prediction System

> AI-powered precision medicine tool that analyzes patient genetic data (VCF files) and predicts personalized drug risks using CPIC guidelines and LLM-generated clinical explanations.

---

## 🔗 Quick Links

| Resource | Link |
|---|---|
| 🌐 Live Demo | [https://pharma-guard.streamlit.app](https://pharma-guard.streamlit.app) |
| 🎥 LinkedIn Demo Video | [Watch on LinkedIn](https://www.linkedin.com/posts/your-video-link) |
| 📁 GitHub Repository | [github.com/yourusername/pharma-guard](https://github.com/yourusername/pharma-guard) |

> 📢 Built for **RIFT 2026 Hackathon** — Pharmacogenomics / Explainable AI Track
> `#RIFT2026` `#PharmaGuard` `#Pharmacogenomics` `#AIinHealthcare`

---

## 📌 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Features](#-features)
- [Supported Genes & Drugs](#-supported-genes--drugs)
- [Installation](#-installation)
- [Usage](#-usage)
- [API / Output Schema](#-output-schema)
- [Sample VCF Files](#-sample-vcf-files)
- [Team](#-team)

---

## 🧬 Problem Statement

Adverse drug reactions kill over **100,000 Americans annually** — many of which are preventable. Pharmacogenomic testing analyzes how a patient's genetic variants affect drug metabolism, enabling clinicians to prescribe the right drug at the right dose for the right patient.

The challenge: there is no accessible, AI-powered tool that takes raw genetic data and instantly produces actionable clinical recommendations with explainable reasoning.

**PharmaGuard solves this.**

---

## 💡 Solution Overview

PharmaGuard is a web application that:

1. Accepts a patient's **VCF (Variant Call Format)** genetic file
2. Identifies pharmacogenomically relevant variants across **6 critical genes**
3. Determines the patient's **diplotype and phenotype** (e.g., Poor Metabolizer)
4. Predicts **drug-specific risk** aligned with CPIC guidelines
5. Generates a **structured clinical explanation** using Claude AI (Anthropic)
6. Outputs a **downloadable JSON report** matching the required clinical schema

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│   File Upload │ Drug Selector │ Results │ JSON Export   │
└───────────────────────┬─────────────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │        Analysis Pipeline    │
         │                             │
         │  VCFParser                  │
         │    └─► VariantMapper        │
         │          └─► DiplotypeCaller│
         │                └─► PhenotypePredictor
         │                      └─► RiskEngine    │
         │                            └─► LLMExplainer
         └─────────────────────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │         Data Layer          │
         │  cpic_guidelines.json       │
         │  variant_database.json      │
         │  diplotype_phenotype.json   │
         └─────────────────────────────┘
                        │
         ┌──────────────▼──────────────┐
         │      Anthropic Claude API   │
         │   (claude-sonnet-4-6)       │
         │  Clinical explanation gen   │
         └─────────────────────────────┘
```

### Pipeline Flow

```
VCF File Upload
     │
     ▼
VCFParser          → Parses variant lines, extracts GENE/STAR/RS INFO tags
     │
     ▼
VariantMapper      → Maps rsIDs to star alleles using variant database
     │
     ▼
DiplotypeCaller    → Pairs alleles into diplotype (e.g., *4/*4)
     │
     ▼
PhenotypePredictor → Lookup-based or activity-score-based phenotype prediction
     │              → PM | IM | NM | RM | URM | Unknown
     ▼
RiskEngine         → CPIC rule lookup: Phenotype + Drug → Risk Label + Action
     │
     ▼
LLMExplainer       → Claude generates mechanism, summary, clinical context
     │
     ▼
JSON Output        → Structured report matching required schema
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend & App | Streamlit |
| Language | Python 3.10+ |
| AI / LLM | Anthropic Claude (claude-sonnet-4-6) |
| Data Validation | Pydantic v2 |
| Data Processing | Pandas |
| Clinical Data | CPIC Guidelines, PharmVar, PharmGKB |
| Deployment | Streamlit Cloud |
| Version Control | GitHub |

---

## ✨ Features

- **VCF File Upload** — drag-and-drop or browse, with size and format validation
- **Multi-drug Analysis** — analyze multiple drugs in a single session
- **Color-coded Risk Display** — Green (Safe), Yellow (Adjust Dosage), Red (Toxic/Ineffective)
- **AI Clinical Explanations** — mechanism, summary, and clinical context per drug
- **Diplotype & Phenotype Calling** — lookup-based with activity-score fallback
- **CPIC-aligned Recommendations** — dose adjustments and alternative drugs
- **Downloadable JSON Reports** — schema-compliant output per drug
- **Quality Metrics** — VCF parse success, annotation completeness, genes analyzed

---

## 🧪 Supported Genes & Drugs

### Genes Analyzed

| Gene | Role |
|---|---|
| CYP2D6 | Codeine, opioid metabolism |
| CYP2C19 | Clopidogrel, antiplatelet activation |
| CYP2C9 | Warfarin dosing |
| SLCO1B1 | Simvastatin hepatic transport |
| TPMT | Azathioprine thiopurine metabolism |
| DPYD | Fluorouracil pyrimidine catabolism |

### Supported Drugs

| Drug | Primary Gene | Key Risk |
|---|---|---|
| CODEINE | CYP2D6 | Respiratory depression (PM/URM) |
| WARFARIN | CYP2C9 | Bleeding risk (PM) |
| CLOPIDOGREL | CYP2C19 | Antiplatelet failure (PM) |
| SIMVASTATIN | SLCO1B1 | Myopathy risk (PM) |
| AZATHIOPRINE | TPMT | Myelosuppression (PM) |
| FLUOROURACIL | DPYD | Severe toxicity (PM) |

### Phenotype Classification

| Code | Name | Activity Score | Meaning |
|---|---|---|---|
| PM | Poor Metabolizer | 0.0 | No/minimal enzyme activity |
| IM | Intermediate Metabolizer | 0.5–1.0 | Reduced enzyme activity |
| NM | Normal Metabolizer | 1.0–2.0 | Standard enzyme activity |
| RM | Rapid Metabolizer | 2.0–3.0 | Increased enzyme activity |
| URM | Ultrarapid Metabolizer | > 3.0 | Greatly increased activity |

---

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- An Anthropic API key ([get one here](https://console.anthropic.com))

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/pharma-guard.git
cd pharma-guard
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 5. Run the App

```bash
streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

---

## 📖 Usage

### Step-by-Step

1. **Upload VCF File** — click or drag a `.vcf` file (max 5MB)
2. **Select Drug(s)** — choose from dropdown or type a custom drug name
3. **Enter Patient ID** — auto-generated UUID or custom input
4. **Click Analyze** — pipeline runs in ~5–10 seconds
5. **View Results** — tabbed display per drug with risk badge, recommendation, AI explanation
6. **Download Report** — JSON report per drug or all results combined

### Using Sample Files

Three sample VCF files are provided in `sample_vcfs/`:

```bash
# Poor Metabolizer — expect Toxic result for CODEINE
sample_vcfs/poor_metabolizer.vcf

# Normal Metabolizer — expect Safe result
sample_vcfs/normal_metabolizer.vcf

# Rapid Metabolizer — expect Ineffective for CLOPIDOGREL
sample_vcfs/rapid_metabolizer.vcf
```

---

## 📋 Output Schema

Every analysis generates a structured JSON report matching this schema:

```json
{
  "patient_id": "PATIENT_A1B2C3D4",
  "drug": "CODEINE",
  "timestamp": "2026-02-19T10:30:00Z",
  "risk_assessment": {
    "risk_label": "Toxic",
    "confidence_score": 0.95,
    "severity": "critical"
  },
  "pharmacogenomic_profile": {
    "primary_gene": "CYP2D6",
    "diplotype": "*4/*4",
    "phenotype": "PM",
    "detected_variants": [
      {
        "rsid": "rs3892097",
        "gene": "CYP2D6",
        "star_allele": "*4",
        "zygosity": "homozygous",
        "clinical_significance": "Poor Metabolizer allele"
      }
    ]
  },
  "clinical_recommendation": {
    "action": "Avoid codeine — life-threatening respiratory depression risk",
    "dose_adjustment": "Contraindicated",
    "alternative_drugs": ["morphine", "hydromorphone"],
    "monitoring_required": true,
    "cpic_guideline_ref": "CPIC Guideline for Codeine and CYP2D6 (2022)"
  },
  "llm_generated_explanation": {
    "summary": "This patient carries two non-functional CYP2D6 alleles (*4/*4), making them a Poor Metabolizer of codeine...",
    "mechanism": "CYP2D6 enzyme converts codeine to morphine via O-demethylation. In PM patients, this conversion is absent...",
    "clinical_context": "Prescribing codeine to this patient risks dangerous morphine accumulation...",
    "references": [
      "CPIC Guideline for Codeine and CYP2D6, 2022",
      "PharmGKB: CYP2D6 variant annotation",
      "Crews et al., Clinical Pharmacology & Therapeutics, 2014"
    ]
  },
  "quality_metrics": {
    "vcf_parsing_success": true,
    "variants_detected": 2,
    "genes_analyzed": ["CYP2D6"],
    "annotation_completeness": 1.0
  }
}
```

### Risk Label Values

| Label | Color | Meaning |
|---|---|---|
| Safe | 🟢 Green | Standard dosing applicable |
| Adjust Dosage | 🟡 Yellow | Dose modification required |
| Toxic | 🔴 Red | High toxicity risk — avoid or contraindicate |
| Ineffective | 🔵 Blue | Drug unlikely to work |
| Unknown | ⚪ Grey | Insufficient pharmacogenomic data |

---

## 📁 Project Structure

```
pharma-guard/
├── app.py                        # Main Streamlit application
├── core/
│   ├── __init__.py
│   ├── vcf_parser.py             # VCF file parsing
│   ├── variant_mapper.py         # rsID → star allele enrichment
│   ├── diplotype_caller.py       # Diplotype determination
│   ├── phenotype_predictor.py    # Phenotype prediction (lookup + score)
│   ├── risk_engine.py            # CPIC-based risk assessment
│   └── llm_explainer.py          # Claude AI explanation generator
├── data/
│   ├── cpic_guidelines.json      # CPIC drug-gene rules
│   ├── variant_database.json     # rsID → star allele lookup
│   └── diplotype_phenotype.json  # Diplotype → Phenotype map
├── models/
│   ├── __init__.py
│   └── schema.py                 # Pydantic output schema
├── sample_vcfs/
│   ├── poor_metabolizer.vcf
│   ├── normal_metabolizer.vcf
│   └── rapid_metabolizer.vcf
├── .env.example
├── requirements.txt
└── README.md
```

---

## ☁️ Deployment

### Streamlit Cloud (Recommended)

1. Push your repo to GitHub (ensure it is **public**)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select repo → branch: `main` → file: `app.py`
5. Under **Advanced Settings**, add secret:
   ```
   ANTHROPIC_API_KEY = sk-ant-your-key-here
   ```
6. Click **Deploy** — live URL in ~2 minutes

---

## 📦 Dependencies

```
streamlit>=1.32.0
anthropic>=0.25.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pandas>=2.0.0
```

Install all with:

```bash
pip install -r requirements.txt
```

---

## 🔬 Clinical References

- [CPIC Guidelines](https://cpicpgx.org) — Clinical Pharmacogenetics Implementation Consortium
- [PharmVar](https://pharmvar.org) — Pharmacogene Variation Consortium (star allele definitions)
- [PharmGKB](https://pharmgkb.org) — Pharmacogenomics Knowledge Base
- [FDA Table of Pharmacogenomic Biomarkers](https://www.fda.gov/medical-devices/precision-medicine/table-pharmacogenomic-biomarkers-drug-labeling)

---

## ⚠️ Disclaimer

PharmaGuard is a **research and educational tool** built for a hackathon. It is **not intended for clinical use**. All pharmacogenomic interpretations should be reviewed by a qualified clinical pharmacist or physician before influencing any prescribing decision.

---

## 👤 Team

| Name | Role |
|---|---|
| Your Name | Full Stack Developer — Solo |

Built with ❤️ for **RIFT 2026 Hackathon** — Pharmacogenomics / Explainable AI Track
