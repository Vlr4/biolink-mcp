#!/usr/bin/env python3
import logging
from typing import Any, Dict, Iterable, List, Optional

from .http import Http
from .mappers import canonical_category

logger = logging.getLogger(__name__)


def _strip_nones(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class BiolinkClient:
    """Thin Biolink API client over Http."""

    def __init__(self, base_url: str = "https://api-v3.monarchinitiative.org/v3/api/"):
        self.http = Http(base_url=base_url)

    async def close(self) -> None:
        await self.http.close()

    # -------- Core endpoints --------

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        return await self.http.get(f"entity/{entity_id}")

    async def search_entities(self, q: str, *, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        params = {"q": q, "limit": limit, "offset": offset}
        return await self.http.get("search", params=params)

    async def associations(
        self,
        entity_id: str,
        category: str,
        *,
        limit: int = 20,
        offset: int = 0,
        max_items: Optional[int] = None,
        evidence_min: Optional[int] = None,
        sources: Optional[Iterable[str]] = None,
        compact: bool = True,
    ) -> Dict[str, Any]:
        """Generic associations fetch with pagination + simple post-filters."""
        cat = canonical_category(category)
        path = f"entity/{entity_id}/{cat}"
        items: List[Dict[str, Any]] = []
        seen = 0
        cur_offset = offset
        per_page = max(1, min(100, limit))  # guardrails

        while True:
            page = await self.http.get(path, params={"limit": per_page, "offset": cur_offset})
            # Biolink v3 returns either "associations" or "items"
            rows = page.get("associations") or page.get("items") or []
            if not isinstance(rows, list):
                rows = []

            items.extend(rows)
            seen += len(rows)
            if max_items is not None and len(items) >= max_items:
                items = items[:max_items]
                break

            # Stop if fewer than requested
            if len(rows) < per_page:
                break
            cur_offset += per_page

        # Post-filters
        if evidence_min is not None:
            items = [r for r in items if (r.get("evidence_count") or 0) >= evidence_min]

        if sources:
            allowed = set(sources)
            items = [r for r in items if (r.get("aggregator_knowledge_source") or r.get("provided_by")) in allowed]

        if not compact:
            return {"items": items, "count": len(items), "category": cat, "entity_id": entity_id}

        shaped = [_strip_nones(self._shape_assoc(r)) for r in items]
        return {"items": shaped, "count": len(shaped), "category": cat, "entity_id": entity_id}

    # -------- Presets (thin wrappers) --------

    async def gene_interactions(self, entity_id: str, **kw) -> Dict[str, Any]:
        return await self.associations(entity_id, "gene-to-gene", **kw)

    async def gene_diseases(self, entity_id: str, **kw) -> Dict[str, Any]:
        return await self.associations(entity_id, "gene-diseases", **kw)

    async def phenotype_genes(self, entity_id: str, **kw) -> Dict[str, Any]:
        return await self.associations(entity_id, "phenotype-genes", **kw)

    # -------- Helpers --------

    def _shape_assoc(self, r: Dict[str, Any]) -> Dict[str, Any]:
        """Compact row with common fields across Biolink association payloads."""
        # Try common subject/object shapes; fall back to top-level ids/labels if present
        subj = r.get("subject") or {}
        obj = r.get("object") or {}

        return {
            "subject_id": subj.get("id") or r.get("subject"),
            "subject_label": subj.get("label") or r.get("subject_label"),
            "predicate": (r.get("predicate") or {}).get("id") if isinstance(r.get("predicate"), dict) else r.get("predicate"),
            "object_id": obj.get("id") or r.get("object"),
            "object_label": obj.get("label") or r.get("object_label"),
            "evidence_count": r.get("evidence_count"),
            "source": r.get("aggregator_knowledge_source") or r.get("provided_by"),
        }
