from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class VCFVariant:
    chrom: str
    pos: int
    rsid: str
    ref: str
    alt: str
    gene: Optional[str]
    star_allele: Optional[str]
    genotype: Optional[str]
    zygosity: Optional[str]

class VCFParser:
    SUPPORTED_GENES = {"CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD"}

    def parse(self, vcf_content: str) -> tuple[List[VCFVariant], dict]:
        variants = []
        quality = {
            "total_lines": 0,
            "parsed_lines": 0,
            "skipped_lines": 0,
            "genes_found": set()
        }

        for line in vcf_content.splitlines():
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                continue
            if not line.strip():
                continue

            quality["total_lines"] += 1
            variant = self._parse_line(line)

            if variant:
                if variant.gene in self.SUPPORTED_GENES or variant.gene is None:
                    variants.append(variant)
                    quality["parsed_lines"] += 1
                    if variant.gene:
                        quality["genes_found"].add(variant.gene)
                else:
                    quality["skipped_lines"] += 1
            else:
                quality["skipped_lines"] += 1

        quality["genes_found"] = list(quality["genes_found"])
        return variants, quality

    def _parse_line(self, line: str) -> Optional[VCFVariant]:
        fields = line.strip().split("\t")
        if len(fields) < 8:
            return None

        chrom, pos, vid, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]
        info = fields[7]
        info_dict = self._parse_info(info)

        genotype, zygosity = None, None
        if len(fields) >= 10:
            gt_raw = fields[9].split(":")[0]
            genotype = gt_raw
            zygosity = self._determine_zygosity(gt_raw)

        return VCFVariant(
            chrom=chrom,
            pos=int(pos) if pos.isdigit() else 0,
            rsid=vid if vid != "." else f"chr{chrom}:{pos}",
            ref=ref,
            alt=alt,
            gene=info_dict.get("GENE"),
            star_allele=info_dict.get("STAR"),
            genotype=genotype,
            zygosity=zygosity
        )

    def _parse_info(self, info: str) -> Dict:
        result = {}
        for field in info.split(";"):
            if "=" in field:
                k, v = field.split("=", 1)
                result[k.strip()] = v.strip()
        return result

    def _determine_zygosity(self, gt: str) -> str:
        alleles = gt.replace("|", "/").split("/")
        if len(alleles) == 2:
            if alleles[0] == alleles[1]:
                return "homozygous" if alleles[0] != "0" else "homozygous_ref"
            elif "0" in alleles:
                return "heterozygous"
            else:
                return "compound_heterozygous"
        return "unknown"