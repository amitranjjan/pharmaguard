from typing import Dict, Tuple

# Full phenotype definitions
PHENOTYPE_DEFINITIONS = {
    "PM":  "Poor Metabolizer — little to no enzyme activity",
    "IM":  "Intermediate Metabolizer — reduced enzyme activity",
    "NM":  "Normal Metabolizer — standard enzyme activity",
    "RM":  "Rapid Metabolizer — increased enzyme activity",
    "URM": "Ultrarapid Metabolizer — greatly increased enzyme activity",
    "Unknown": "Phenotype could not be determined from available data"
}

# Effect → Phenotype contribution mapping
EFFECT_SCORE = {
    "loss_of_function":      0,     # no activity
    "decreased_function":    0.5,   # half activity
    "normal_function":       1.0,   # full activity
    "increased_function":    1.5,   # more than normal
    "unknown":               1.0    # assume normal if unknown
}

# Score thresholds per gene (some genes differ)
# Based on CPIC activity score framework (especially CYP2D6)
SCORE_TO_PHENOTYPE = [
    (0.0,  0.0,  "PM"),   # total score = 0
    (0.01, 1.0,  "IM"),   # score > 0 and <= 1.0
    (1.01, 2.0,  "NM"),   # score > 1.0 and <= 2.0
    (2.01, 3.0,  "RM"),   # score > 2.0 and <= 3.0
    (3.01, 99.0, "URM"),  # score > 3.0
]


class PhenotypePredictor:
    """
    Two prediction strategies:
    1. Lookup-based  — use diplotype_phenotype.json (fast, accurate for known diplotypes)
    2. Score-based   — use activity scores per allele (fallback for unknown diplotypes)
    """

    def predict(
        self,
        gene: str,
        diplotype: str,
        lookup_result: str,
        enriched_variants: list
    ) -> Dict:
        """
        Primary entry point. Returns a full phenotype dict.
        lookup_result comes from DiplotypeCaller (may be 'Unknown').
        """

        if lookup_result and lookup_result != "Unknown":
            return self._build_result(
                phenotype=lookup_result,
                method="diplotype_lookup",
                diplotype=diplotype,
                gene=gene
            )

        # Fallback: score-based prediction
        score_phenotype, score = self._score_based(gene, enriched_variants)
        return self._build_result(
            phenotype=score_phenotype,
            method="activity_score",
            diplotype=diplotype,
            gene=gene,
            activity_score=score
        )

    def _score_based(self, gene: str, enriched_variants: list) -> Tuple[str, float]:
        """
        Calculate total activity score from all detected variants for this gene.
        Each allele contributes based on its effect type.
        Zygosity determines if we count once (het) or twice (hom).
        """
        gene_variants = [v for v in enriched_variants if v.get("gene") == gene]

        if not gene_variants:
            # No variants = wildtype = Normal Metabolizer
            return "NM", 2.0

        total_score = 0.0

        for v in gene_variants:
            effect = v.get("effect", "unknown")
            zygosity = v.get("zygosity", "unknown")
            allele_score = EFFECT_SCORE.get(effect, 1.0)

            if zygosity == "homozygous":
                total_score += allele_score * 2
            elif zygosity in ("heterozygous", "compound_heterozygous"):
                total_score += allele_score
                total_score += 1.0                
            else:
                total_score += allele_score        

        phenotype = self._score_to_phenotype(total_score)
        return phenotype, round(total_score, 2)

    def _score_to_phenotype(self, score: float) -> str:
        for low, high, phenotype in SCORE_TO_PHENOTYPE:
            if low <= score <= high:
                return phenotype
        return "Unknown"

    def _build_result(
        self,
        phenotype: str,
        method: str,
        diplotype: str,
        gene: str,
        activity_score: float = None
    ) -> Dict:
        return {
            "phenotype": phenotype,
            "phenotype_definition": PHENOTYPE_DEFINITIONS.get(phenotype, "Unknown phenotype"),
            "prediction_method": method,
            "gene": gene,
            "diplotype": diplotype,
            "activity_score": activity_score,  
            "is_actionable": phenotype != "NM"  
        }


def get_phenotype_label(phenotype: str) -> str:
    return PHENOTYPE_DEFINITIONS.get(phenotype, "Unknown")

def is_rapid_metabolizer(phenotype: str) -> bool:
    return phenotype in ("RM", "URM")

def is_poor_metabolizer(phenotype: str) -> bool:
    return phenotype == "PM"

def phenotype_risk_direction(phenotype: str) -> str:
    """
    Returns whether the phenotype causes too much or too little drug effect.
    Useful for LLM prompt context.
    """
    directions = {
        "PM":  "reduced_clearance",   
        "IM":  "reduced_clearance",   
        "NM":  "normal",
        "RM":  "increased_clearance", 
        "URM": "increased_clearance", 
    }
    return directions.get(phenotype, "unknown")

