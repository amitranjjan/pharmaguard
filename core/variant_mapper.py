import json
from pathlib import Path
from core.vcf_parser import VCFVariant
from typing import List, Dict

class VariantMapper:
    def __init__(self):
        db_path = Path("data/variant_database.json")
        with open(db_path) as f:
            self.db = json.load(f)

    def enrich_variants(self, variants: List[VCFVariant]) -> List[Dict]:
        enriched = []
        for v in variants:
            rsid_lower = v.rsid.lower()
            db_entry = self.db.get(rsid_lower) or self.db.get(v.rsid)

            if db_entry:
                enriched.append({
                    "rsid": v.rsid,
                    "gene": db_entry.get("gene", v.gene or "Unknown"),
                    "star_allele": db_entry.get("star_allele", v.star_allele or "Unknown"),
                    "zygosity": v.zygosity or "unknown",
                    "effect": db_entry.get("effect", "unknown"),
                    "clinical_significance": db_entry.get("clinical_significance", ""),
                    "chrom": v.chrom,
                    "pos": v.pos,
                    "ref": v.ref,
                    "alt": v.alt,
                    "genotype": v.genotype,
                    "source": "database"
                })
            elif v.gene and v.star_allele:
                # INFO tags provided directly in VCF
                enriched.append({
                    "rsid": v.rsid,
                    "gene": v.gene,
                    "star_allele": v.star_allele,
                    "zygosity": v.zygosity or "unknown",
                    "effect": "unknown",
                    "clinical_significance": "Annotated in VCF",
                    "chrom": v.chrom,
                    "pos": v.pos,
                    "ref": v.ref,
                    "alt": v.alt,
                    "genotype": v.genotype,
                    "source": "vcf_annotation"
                })

        return enriched