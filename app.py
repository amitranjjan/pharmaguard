import streamlit as st
import json
import uuid
from datetime import datetime
from pathlib import Path

from core.vcf_parser import VCFParser
from core.variant_mapper import VariantMapper
from core.diplotype_caller import DiplotypeCaller
from core.risk_engine import RiskEngine
from core.llm_explainer import generate_explanation
from models.schema import PharmaGuardOutput

# Page config
st.set_page_config(
    page_title="PharmaGuard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Styling
st.markdown("""
<style>
    .risk-safe     { background:#d4edda; color:#155724; padding:8px 16px; border-radius:8px; font-weight:bold; font-size:1.2em; }
    .risk-adjust   { background:#fff3cd; color:#856404; padding:8px 16px; border-radius:8px; font-weight:bold; font-size:1.2em; }
    .risk-toxic    { background:#f8d7da; color:#721c24; padding:8px 16px; border-radius:8px; font-weight:bold; font-size:1.2em; }
    .risk-ineffective { background:#d1ecf1; color:#0c5460; padding:8px 16px; border-radius:8px; font-weight:bold; font-size:1.2em; }
    .risk-unknown  { background:#e2e3e5; color:#383d41; padding:8px 16px; border-radius:8px; font-weight:bold; font-size:1.2em; }
    .metric-box    { background:#f8f9fa; padding:16px; border-radius:8px; border-left:4px solid #0d6efd; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

RISK_CSS = {
    "Safe": "risk-safe",
    "Adjust Dosage": "risk-adjust",
    "Toxic": "risk-toxic",
    "Ineffective": "risk-ineffective",
    "Unknown": "risk-unknown"
}

SUPPORTED_DRUGS = ["CODEINE", "WARFARIN", "CLOPIDOGREL", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"]

# Initialize modules 
@st.cache_resource
def load_modules():
    return VCFParser(), VariantMapper(), DiplotypeCaller(), RiskEngine()

parser, mapper, caller, engine = load_modules()

# Header 
st.title("💊 PharmaGuard")
st.markdown("**Pharmacogenomic Risk Prediction System** — Powered by TEAM xSparx")
st.divider()

# Input Section 
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📁 Upload VCF File")
    vcf_file = st.file_uploader(
        "Drag and drop or browse",
        type=["vcf"],
        help="Upload a VCF v4.2 file (max 5MB). Must contain GENE and STAR INFO tags."
    )
    if vcf_file:
        size_kb = vcf_file.size / 1024
        if vcf_file.size > 5 * 1024 * 1024:
            st.error("File exceeds 5MB limit.")
            vcf_file = None
        else:
            st.success(f"✅ {vcf_file.name} ({size_kb:.1f} KB)")

with col2:
    st.subheader("💉 Select Drug(s)")
    selected_drugs = st.multiselect(
        "Choose one or more drugs",
        options=SUPPORTED_DRUGS,
        default=["CODEINE"],
        help="Select drugs to analyze. Multiple drugs generate separate reports."
    )
    custom_drug = st.text_input(
        "Or type a custom drug name",
        placeholder="e.g., TAMOXIFEN",
        help="For drugs not in the list. Results may have limited CPIC data."
    )
    if custom_drug:
        selected_drugs.append(custom_drug.upper().strip())

    patient_id = st.text_input(
        "Patient ID (optional)",
        value=f"PATIENT_{str(uuid.uuid4())[:8].upper()}",
        help="Auto-generated if left blank"
    )

st.divider()

# Analyze Button 
analyze_btn = st.button(
    "🔬 Analyze Pharmacogenomic Risk",
    type="primary",
    use_container_width=True,
    disabled=(vcf_file is None or len(selected_drugs) == 0)
)

# Analysis Pipeline 
if analyze_btn and vcf_file:
    results = []

    with st.spinner("Parsing VCF and analyzing variants..."):
        vcf_content = vcf_file.read().decode("utf-8")
        variants, quality_info = parser.parse(vcf_content)
        enriched = mapper.enrich_variants(variants)

    for drug in selected_drugs:
        with st.spinner(f"Analyzing {drug}..."):
            primary_gene = engine.get_primary_gene(drug)
            diplotype, phenotype = caller.call_diplotype(enriched, primary_gene)
            risk = engine.assess_risk(drug, phenotype, primary_gene)

        with st.spinner(f"Generating AI explanation for {drug}..."):
            explanation = generate_explanation(
                gene=primary_gene,
                diplotype=diplotype,
                phenotype=phenotype,
                drug=drug,
                risk_label=risk["risk_label"],
                severity=risk["severity"],
                action=risk["action"],
                variants=enriched
            )

        # Build output
        gene_variants = [v for v in enriched if v.get("gene") == primary_gene]
        completeness = len(gene_variants) / max(len(enriched), 1) if enriched else 0.0

        output = {
            "patient_id": patient_id,
            "drug": drug,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "risk_assessment": {
                "risk_label": risk["risk_label"],
                "confidence_score": risk["confidence_score"],
                "severity": risk["severity"]
            },
            "pharmacogenomic_profile": {
                "primary_gene": primary_gene,
                "diplotype": diplotype,
                "phenotype": phenotype,
                "detected_variants": [
                    {
                        "rsid": v["rsid"],
                        "gene": v["gene"],
                        "star_allele": v["star_allele"],
                        "zygosity": v["zygosity"],
                        "clinical_significance": v.get("clinical_significance", "")
                    } for v in gene_variants
                ]
            },
            "clinical_recommendation": {
                "action": risk["action"],
                "dose_adjustment": risk["dose_adjustment"],
                "alternative_drugs": risk["alternatives"],
                "monitoring_required": risk["monitoring_required"],
                "cpic_guideline_ref": risk["cpic_ref"]
            },
            "llm_generated_explanation": explanation,
            "quality_metrics": {
                "vcf_parsing_success": len(variants) > 0,
                "variants_detected": len(enriched),
                "genes_analyzed": list(set(v["gene"] for v in enriched)),
                "annotation_completeness": round(completeness, 2)
            }
        }
        results.append(output)

    st.session_state["results"] = results
    st.session_state["enriched"] = enriched

# Results Display 
if "results" in st.session_state:
    st.divider()
    st.subheader("📊 Results")

    results = st.session_state["results"]
    enriched = st.session_state["enriched"]

    tabs = st.tabs([f"💊 {r['drug']}" for r in results] + ["📋 All JSON"])

    for i, result in enumerate(results):
        with tabs[i]:
            r = result
            ra = r["risk_assessment"]
            pgx = r["pharmacogenomic_profile"]
            cr = r["clinical_recommendation"]
            llm = r["llm_generated_explanation"]
            qm = r["quality_metrics"]

            # Risk Badge
            css_class = RISK_CSS.get(ra["risk_label"], "risk-unknown")
            st.markdown(
                f'<div class="{css_class}">⚠️ Risk: {ra["risk_label"]} &nbsp;|&nbsp; '
                f'Severity: {ra["severity"].upper()} &nbsp;|&nbsp; '
                f'Confidence: {ra["confidence_score"]*100:.0f}%</div>',
                unsafe_allow_html=True
            )
            st.markdown("")

            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Gene", pgx["primary_gene"])
            m2.metric("Diplotype", pgx["diplotype"])
            m3.metric("Phenotype", pgx["phenotype"])
            m4.metric("Variants Found", qm["variants_detected"])

            st.divider()

            # Clinical Recommendation
            with st.expander("🏥 Clinical Recommendation", expanded=True):
                st.markdown(f"**Action:** {cr['action']}")
                st.markdown(f"**Dose Adjustment:** {cr['dose_adjustment']}")
                if cr["alternative_drugs"]:
                    st.markdown(f"**Alternatives:** {', '.join(cr['alternative_drugs'])}")
                st.markdown(f"**Monitoring Required:** {'Yes ⚠️' if cr['monitoring_required'] else 'No ✅'}")
                st.caption(f"📚 {cr['cpic_guideline_ref']}")

            # AI Explanation
            with st.expander("🤖 AI-Generated Clinical Explanation", expanded=True):
                st.markdown("**Summary**")
                st.info(llm.get("summary", "N/A"))
                st.markdown("**Biological Mechanism**")
                st.write(llm.get("mechanism", "N/A"))
                st.markdown("**Clinical Context**")
                st.write(llm.get("clinical_context", "N/A"))
                st.markdown("**References**")
                for ref in llm.get("references", []):
                    st.markdown(f"- {ref}")

            # Detected Variants Table
            with st.expander("🧬 Detected Variants"):
                if pgx["detected_variants"]:
                    import pandas as pd
                    df = pd.DataFrame(pgx["detected_variants"])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No variants detected for this gene — assuming wildtype (*1/*1)")

            # Quality Metrics
            with st.expander("📈 Quality Metrics"):
                q1, q2 = st.columns(2)
                q1.metric("VCF Parse Success", "✅ Yes" if qm["vcf_parsing_success"] else "❌ No")
                q1.metric("Genes Analyzed", ", ".join(qm["genes_analyzed"]) or "None")
                q2.metric("Annotation Completeness", f"{qm['annotation_completeness']*100:.0f}%")
                st.progress(qm["annotation_completeness"])

            # Download
            st.divider()
            json_str = json.dumps(r, indent=2)
            st.download_button(
                label="⬇️ Download JSON Report",
                data=json_str,
                file_name=f"pharma_guard_{r['patient_id']}_{r['drug']}.json",
                mime="application/json",
                use_container_width=True
            )
            if st.button(f"📋 Copy to Clipboard ({r['drug']})", key=f"copy_{i}"):
                st.code(json_str, language="json")

    # All JSON tab
    with tabs[-1]:
        all_json = json.dumps(results, indent=2)
        st.json(results)
        st.download_button(
            label="⬇️ Download All Results (JSON)",
            data=all_json,
            file_name=f"pharma_guard_all_{patient_id}.json",
            mime="application/json",
            use_container_width=True
        )