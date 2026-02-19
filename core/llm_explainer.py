import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini 
genai.configure(api_key=os.getenv("API key here"))
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0.3,       # low temp = consistent clinical output
        "top_p": 0.95,
        "max_output_tokens": 1000,
    }
)

# Drug type lookup (prodrug vs active) 
DRUG_TYPE = {
    "CODEINE":       "prodrug",      
    "CLOPIDOGREL":   "prodrug",     
    "WARFARIN":      "active_drug",  
    "SIMVASTATIN":   "active_drug", 
    "AZATHIOPRINE":  "prodrug",    
    "FLUOROURACIL":  "active_drug" 
}

# Phenotype definitions for richer prompts
PHENOTYPE_DEFINITIONS = {
    "PM":      "Poor Metabolizer — little to no enzyme activity",
    "IM":      "Intermediate Metabolizer — reduced enzyme activity",
    "NM":      "Normal Metabolizer — standard enzyme activity",
    "RM":      "Rapid Metabolizer — increased enzyme activity",
    "URM":     "Ultrarapid Metabolizer — greatly increased enzyme activity",
    "Unknown": "Phenotype could not be determined"
}

# Prompt template 
PROMPT_TEMPLATE = """You are a clinical pharmacogenomics expert writing explanations for licensed physicians.

PATIENT PHARMACOGENOMIC DATA:
- Gene analyzed      : {gene}
- Diplotype          : {diplotype}
- Phenotype          : {phenotype} ({phenotype_definition})
- Activity Score     : {activity_score}
- Drug               : {drug}
- Drug Type          : {drug_type}
- Risk Assessment    : {risk_label} (Severity: {severity})
- Recommended Action : {action}
- Detected Variants  : {variants}

INSTRUCTIONS:
- Write for a physician audience using clinical terminology
- Mention the specific gene, diplotype, and variant rsIDs
- Explain WHY this phenotype causes this specific risk for this specific drug
- For prodrugs: explain activation pathway and what goes wrong
- For active drugs: explain clearance pathway and what goes wrong
- Keep each field concise but medically complete
- Do NOT include markdown, code fences, or backticks in your response

Respond ONLY with this exact JSON structure and nothing else:
{{
  "summary": "2-3 sentence plain-language explanation of the risk for this patient",
  "mechanism": "Detailed biological mechanism — mention enzyme, metabolic pathway, and effect on drug plasma levels",
  "clinical_context": "Practical prescribing implications — what the clinician should do and why",
  "references": [
    "CPIC guideline reference",
    "PharmGKB or PharmVar reference",
    "Key supporting clinical study"
  ]
}}"""


def generate_explanation(
    gene: str,
    diplotype: str,
    phenotype: str,
    drug: str,
    risk_label: str,
    severity: str,
    action: str,
    variants: list,
    activity_score: float = None
) -> dict:
    """
    Generate LLM-based clinical explanation using Gemini Flash.

    Returns a dict with keys:
    - summary
    - mechanism
    - clinical_context
    - references
    """

    # Format variant list for prompt
    variant_str = _format_variants(variants, gene)

    # Build prompt
    prompt = PROMPT_TEMPLATE.format(
        gene=gene,
        diplotype=diplotype,
        phenotype=phenotype,
        phenotype_definition=PHENOTYPE_DEFINITIONS.get(phenotype, "Unknown phenotype"),
        activity_score=activity_score if activity_score is not None else "Not calculated",
        drug=drug.upper(),
        drug_type=DRUG_TYPE.get(drug.upper(), "unknown"),
        risk_label=risk_label,
        severity=severity,
        action=action,
        variants=variant_str
    )

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        cleaned = _clean_response(raw)
        result = json.loads(cleaned)

        # Validate all required keys exist
        result = _validate_and_fill(result, gene, diplotype, phenotype, drug, risk_label, action)
        return result

    except json.JSONDecodeError:
        # Gemini returned non-JSON — use structured fallback
        return _fallback_explanation(gene, diplotype, phenotype, drug, risk_label, action)

    except Exception as e:
        # API error, quota exceeded, network issue etc.
        print(f"[LLM Error] {type(e).__name__}: {e}")
        return _fallback_explanation(gene, diplotype, phenotype, drug, risk_label, action)


# Helper functions

def _format_variants(variants: list, gene: str) -> str:
    """Format detected variants into a readable string for the prompt."""
    gene_variants = [v for v in variants if v.get("gene") == gene]

    if not gene_variants:
        return "No variants detected (assumed wildtype)"

    formatted = []
    for v in gene_variants[:4]:
        rsid = v.get("rsid", "unknown")
        star = v.get("star_allele", "?")
        zygosity = v.get("zygosity", "unknown")
        effect = v.get("effect", "unknown")
        formatted.append(f"{rsid} ({star}, {zygosity}, {effect})")

    return " | ".join(formatted)


def _clean_response(raw: str) -> str:
    """Remove markdown fences if Gemini wraps response in them."""
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]

    # Remove any leading/trailing whitespace
    return raw.strip()


def _validate_and_fill(result: dict, gene, diplotype, phenotype, drug, risk_label, action) -> dict:
    """Ensure all required keys are present in the response."""
    required_keys = ["summary", "mechanism", "clinical_context", "references"]
    fallback = _fallback_explanation(gene, diplotype, phenotype, drug, risk_label, action)

    for key in required_keys:
        if key not in result or not result[key]:
            result[key] = fallback[key]

    # Ensure references is a list
    if not isinstance(result.get("references"), list):
        result["references"] = fallback["references"]

    return result


def _fallback_explanation(gene, diplotype, phenotype, drug, risk_label, action) -> dict:
    """
    Rule-based fallback used when Gemini API fails or returns invalid JSON.
    Covers all major gene-phenotype-drug combinations.
    """
    drug_upper = drug.upper()
    key = (gene, phenotype, drug_upper)

    hardcoded = {
        ("CYP2D6", "PM", "CODEINE"): {
            "summary": f"This patient carries the {diplotype} CYP2D6 diplotype, classifying them as a Poor Metabolizer. Codeine is contraindicated due to the inability to convert it to morphine, with risk of respiratory depression from toxic metabolite accumulation.",
            "mechanism": "CYP2D6 catalyzes the O-demethylation of codeine to morphine. The *4 allele introduces a splicing defect resulting in a non-functional enzyme. In *4/*4 homozygotes, this conversion is completely absent, causing codeine accumulation and preventing analgesic effect while increasing toxic metabolite burden.",
            "clinical_context": "Prescribing codeine to this patient is contraindicated per CPIC guidelines. Switch to morphine or hydromorphone, which are not CYP2D6-dependent. Document the genetic finding in the patient's chart.",
            "references": ["CPIC Guideline for Codeine and CYP2D6 (2022)", "PharmGKB: PA166104996", "Crews et al., Clin Pharmacol Ther 2014"]
        },
        ("CYP2D6", "URM", "CODEINE"): {
            "summary": f"Patient is a CYP2D6 Ultrarapid Metabolizer ({diplotype}). Codeine is rapidly converted to morphine at dangerously high rates, risking fatal respiratory depression.",
            "mechanism": "Gene duplication or multiplication of functional CYP2D6 alleles leads to greatly amplified enzyme activity. Codeine is metabolized to morphine far faster than normal, flooding the system with active opioid.",
            "clinical_context": "Codeine is contraindicated in URM patients. Even standard doses can cause life-threatening opioid toxicity. Use non-opioid alternatives or opioids not metabolized by CYP2D6.",
            "references": ["CPIC Guideline for Codeine and CYP2D6 (2022)", "FDA Drug Safety Communication on Codeine"]
        },
        ("CYP2C19", "PM", "CLOPIDOGREL"): {
            "summary": f"This patient is a CYP2C19 Poor Metabolizer ({diplotype}). Clopidogrel cannot be converted to its active form, rendering it ineffective as an antiplatelet agent.",
            "mechanism": "CYP2C19 activates clopidogrel via two-step oxidation to an active thiol metabolite that irreversibly inhibits the P2Y12 platelet receptor. In PM patients, this activation pathway is blocked, resulting in no platelet inhibition.",
            "clinical_context": "Switch to prasugrel or ticagrelor, which do not require CYP2C19 activation. These alternatives provide reliable antiplatelet effect regardless of CYP2C19 status.",
            "references": ["CPIC Guideline for Clopidogrel and CYP2C19 (2022)", "PharmGKB: PA166104999"]
        },
        ("CYP2C9", "PM", "WARFARIN"): {
            "summary": f"Patient is a CYP2C9 Poor Metabolizer ({diplotype}). Warfarin clearance is severely reduced, causing drug accumulation and elevated bleeding risk at standard doses.",
            "mechanism": "CYP2C9 is the primary enzyme responsible for S-warfarin hydroxylation and clearance. Loss-of-function alleles reduce enzyme activity, prolonging warfarin half-life and increasing anticoagulant effect at standard doses.",
            "clinical_context": "Reduce initial warfarin dose by 50-75%. Increase INR monitoring frequency during initiation phase. Consider using a pharmacogenomic dosing algorithm.",
            "references": ["CPIC Guideline for Warfarin (2017)", "PharmGKB: PA166104979", "IWPC Warfarin Dosing Algorithm"]
        },
        ("SLCO1B1", "PM", "SIMVASTATIN"): {
            "summary": f"Patient has reduced SLCO1B1 transporter function ({diplotype}), impairing hepatic uptake of simvastatin and raising plasma drug levels with high myopathy risk.",
            "mechanism": "SLCO1B1 encodes the OATP1B1 hepatic uptake transporter. The *5 variant reduces transporter activity, causing simvastatin to remain in systemic circulation at elevated concentrations, increasing skeletal muscle exposure and toxicity risk.",
            "clinical_context": "Avoid high-dose simvastatin. Switch to pravastatin or rosuvastatin which are less dependent on SLCO1B1 transport. If simvastatin is continued, cap at 20mg/day and monitor for muscle symptoms.",
            "references": ["CPIC Guideline for Simvastatin and SLCO1B1 (2022)", "PharmGKB: PA166105003"]
        },
        ("TPMT", "PM", "AZATHIOPRINE"): {
            "summary": f"Patient is a TPMT Poor Metabolizer ({diplotype}). Azathioprine cannot be safely metabolized, causing life-threatening myelosuppression at standard doses.",
            "mechanism": "TPMT inactivates thiopurine drugs by S-methylation. In PM patients, lack of TPMT activity causes accumulation of cytotoxic 6-thioguanine nucleotides in hematopoietic cells, leading to severe bone marrow suppression.",
            "clinical_context": "Azathioprine is contraindicated at standard doses. If thiopurine therapy is necessary, reduce dose to 10% of standard and monitor CBC weekly. Consider switching to mycophenolate mofetil.",
            "references": ["CPIC Guideline for Thiopurines and TPMT (2022)", "PharmGKB: PA166104984"]
        },
        ("DPYD", "PM", "FLUOROURACIL"): {
            "summary": f"Patient is a DPYD Poor Metabolizer ({diplotype}). Fluorouracil cannot be adequately catabolized, resulting in severe and potentially fatal drug toxicity.",
            "mechanism": "DPYD (dihydropyrimidine dehydrogenase) is responsible for >80% of fluorouracil catabolism. Loss-of-function variants cause fluorouracil accumulation, leading to severe gastrointestinal, hematological, and neurological toxicity.",
            "clinical_context": "Fluorouracil is contraindicated in DPYD PM patients. If fluoropyrimidine therapy is unavoidable, reduce dose by 50% minimum under specialist supervision with close toxicity monitoring.",
            "references": ["CPIC Guideline for Fluoropyrimidines and DPYD (2023)", "PharmGKB: PA166109603"]
        }
    }

    if key in hardcoded:
        return hardcoded[key]

    # Generic fallback for any unknown combo
    return {
        "summary": f"Patient has {gene} {diplotype} diplotype ({phenotype} phenotype), resulting in {risk_label} risk for {drug}. {action}",
        "mechanism": f"{gene} enzyme activity is altered by the {diplotype} diplotype. This directly affects the metabolism of {drug}, changing its plasma concentration and clinical effect.",
        "clinical_context": action,
        "references": [
            "CPIC Guidelines — cpicpgx.org",
            "PharmGKB — pharmgkb.org",
            "PharmVar — pharmvar.org"
        ]

    }
