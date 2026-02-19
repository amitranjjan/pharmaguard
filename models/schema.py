from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DetectedVariant(BaseModel):
    rsid: str
    gene: str
    star_allele: str
    zygosity: str
    clinical_significance: str

class RiskAssessment(BaseModel):
    risk_label: str
    confidence_score: float
    severity: str

class PharmacogenomicProfile(BaseModel):
    primary_gene: str
    diplotype: str
    phenotype: str
    detected_variants: List[DetectedVariant]

class ClinicalRecommendation(BaseModel):
    action: str
    dose_adjustment: str
    alternative_drugs: List[str]
    monitoring_required: bool
    cpic_guideline_ref: str

class LLMExplanation(BaseModel):
    summary: str
    mechanism: str
    clinical_context: str
    references: List[str]

class QualityMetrics(BaseModel):
    vcf_parsing_success: bool
    variants_detected: int
    genes_analyzed: List[str]
    annotation_completeness: float

class PharmaGuardOutput(BaseModel):
    patient_id: str
    drug: str
    timestamp: str
    risk_assessment: RiskAssessment
    pharmacogenomic_profile: PharmacogenomicProfile
    clinical_recommendation: ClinicalRecommendation
    llm_generated_explanation: LLMExplanation
    quality_metrics: QualityMetrics