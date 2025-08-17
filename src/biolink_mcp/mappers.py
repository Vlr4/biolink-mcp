#!/usr/bin/env python3
from typing import Dict

# Friendly aliases → canonical Biolink categories
CATEGORY_ALIASES: Dict[str, str] = {
    # you can extend/adjust as you like
    "gene-to-gene": "biolink:PairwiseGeneToGeneInteraction",
    "interactions": "biolink:PairwiseGeneToGeneInteraction",
    "gene-interactions": "biolink:PairwiseGeneToGeneInteraction",

    "gene-diseases": "biolink:CausalGeneToDiseaseAssociation",
    "gene-to-disease": "biolink:CausalGeneToDiseaseAssociation",

    "gene-phenotypes": "biolink:GeneToPhenotypicFeatureAssociation",
    "phenotype-genes": "biolink:GeneToPhenotypicFeatureAssociation",
}

def canonical_category(value: str) -> str:
    key = value.strip().lower().replace(" ", "-").replace("_", "-")
    return CATEGORY_ALIASES.get(key, value)
