import json
from pathlib import Path
from typing import Dict

class RiskEngine:
    def __init__(self):
        with open(Path("data/cpic_guidelines.json")) as f:
            self.guidelines = json.load(f)

    def assess_risk(self, drug: str, phenotype: str, gene: str) -> Dict:
        drug_upper = drug.upper().strip()

        if drug_upper not in self.guidelines:
            return self._unknown_drug(drug_upper)

        drug_rules = self.guidelines[drug_upper]
        rules = drug_rules.get("rules", {})
        rule = rules.get(phenotype, rules.get("Unknown", self._default_rule()))

        return {
            "drug": drug_upper,
            "gene": drug_rules.get("primary_gene", gene),
            "cpic_ref": drug_rules.get("cpic_ref", ""),
            "risk_label": rule["risk_label"],
            "severity": rule["severity"],
            "confidence_score": rule["confidence"],
            "action": rule["action"],
            "dose_adjustment": rule.get("dose_adjustment", "Consult clinician"),
            "alternatives": rule.get("alternatives", []),
            "monitoring_required": rule.get("monitoring", False)
        }

    def get_primary_gene(self, drug: str) -> str:
        return self.guidelines.get(drug.upper(), {}).get("primary_gene", "Unknown")

    def _unknown_drug(self, drug: str) -> Dict:
        return {
            "drug": drug,
            "gene": "Unknown",
            "cpic_ref": "No CPIC guideline available",
            "risk_label": "Unknown",
            "severity": "low",
            "confidence_score": 0.30,
            "action": "No pharmacogenomic guideline available for this drug",
            "dose_adjustment": "Standard clinical judgment",
            "alternatives": [],
            "monitoring_required": True
        }

    def _default_rule(self) -> Dict:
        return {
            "risk_label": "Unknown",
            "severity": "low",
            "confidence": 0.40,
            "action": "Insufficient data",
            "dose_adjustment": "Consult pharmacist",
            "alternatives": [],
            "monitoring": True
        }