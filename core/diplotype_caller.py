import json
from pathlib import Path
from typing import List, Dict, Tuple

class DiplotypeCaller:
    def __init__(self):
        with open(Path("data/diplotype_phenotype.json")) as f:
            self.dp_map = json.load(f)

    def call_diplotype(self, enriched_variants: List[Dict], gene: str) -> Tuple[str, str]:
        gene_variants = [v for v in enriched_variants if v.get("gene") == gene]

        if not gene_variants:
            default_diplotype = self.dp_map.get(gene, {}).get("default_no_variant", "*1/*1")
            default_phenotype = self.dp_map.get(gene, {}).get("default_phenotype", "NM")
            return default_diplotype, default_phenotype

        star_alleles = []
        for v in gene_variants:
            sa = v.get("star_allele", "Unknown")
            zygosity = v.get("zygosity", "unknown")
            if sa and sa != "Unknown":
                if zygosity == "homozygous":
                    star_alleles.extend([sa, sa])
                else:
                    star_alleles.append(sa)

        if not star_alleles:
            return "*1/*1", "NM"

        # Pair alleles
        if len(star_alleles) == 1:
            diplotype = f"*1/{star_alleles[0]}"
        elif len(star_alleles) >= 2:
            diplotype = f"{star_alleles[0]}/{star_alleles[1]}"
        else:
            diplotype = "*1/*1"

        # Look up phenotype
        gene_map = self.dp_map.get(gene, {})
        phenotype = gene_map.get(diplotype)

        # Try reversed
        if not phenotype:
            parts = diplotype.split("/")
            reversed_dip = f"{parts[1]}/{parts[0]}"
            phenotype = gene_map.get(reversed_dip, "Unknown")

        return diplotype, phenotype