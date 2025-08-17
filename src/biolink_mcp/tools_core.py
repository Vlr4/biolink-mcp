#!/usr/bin/env python3
import asyncio
import logging
import time
from typing import Any, Dict, Iterable, Optional

from .client import BiolinkClient

logger = logging.getLogger(__name__)


class BiolinkTools:
    """MCP glue: registers tools and forwards to BiolinkClient."""

    def __init__(self, mcp_server, prefix: str = "biolink_", base_url: str = "https://api-v3.monarchinitiative.org/v3/api/"):
        self.mcp_server = mcp_server
        self.prefix = prefix
        self.client = BiolinkClient(base_url=base_url)

    # ---------- Tool handlers ----------

    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Fetch an entity by its ID from the Biolink API."""
        return await self.client.get_entity(entity_id)

    async def search_entities(self, q: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Search for entities by label. Args: q (query), limit, offset."""
        return await self.client.search_entities(q, limit=limit, offset=offset)

    async def associations(
        self,
        entity_id: str,
        category: str,
        limit: int = 20,
        offset: int = 0,
        max_items: Optional[int] = None,
        evidence_min: Optional[int] = None,
        sources: Optional[Iterable[str]] = None,
        compact: bool = True,
    ) -> Dict[str, Any]:
        """Retrieve associations for an entity + category (aliases accepted)."""
        return await self.client.associations(
            entity_id,
            category,
            limit=limit,
            offset=offset,
            max_items=max_items,
            evidence_min=evidence_min,
            sources=sources,
            compact=compact,
        )

    async def gene_interactions(self, entity_id: str, **kw) -> Dict[str, Any]:
        """Preset: gene-to-gene interactions."""
        return await self.client.gene_interactions(entity_id, **kw)

    async def gene_diseases(self, entity_id: str, **kw) -> Dict[str, Any]:
        """Preset: causal gene→disease associations."""
        return await self.client.gene_diseases(entity_id, **kw)

    async def phenotype_genes(self, entity_id: str, **kw) -> Dict[str, Any]:
        """Preset: gene↔phenotypic feature associations."""
        return await self.client.phenotype_genes(entity_id, **kw)

    async def health_check(self) -> Dict[str, Any]:
        """Ping the API and report basic health/latency."""
        t0 = time.perf_counter()
        try:
            _ = await self.client.search_entities("TP53", limit=1, offset=0)
            ok = True
            detail = "ok"
        except Exception as e:
            ok = False
            detail = f"{type(e).__name__}: {e}"
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {"ok": ok, "latency_ms": latency_ms, "detail": detail}

    async def close(self) -> None:
        await self.client.close()

    # ---------- Registration ----------

    def register_tools(self):
        self.mcp_server.tool(name=f"{self.prefix}get_entity", description=self.get_entity.__doc__)(self.get_entity)
        self.mcp_server.tool(name=f"{self.prefix}search_entities", description=self.search_entities.__doc__)(self.search_entities)
        self.mcp_server.tool(name=f"{self.prefix}associations", description=self.associations.__doc__)(self.associations)
        self.mcp_server.tool(name=f"{self.prefix}gene_interactions", description=self.gene_interactions.__doc__)(self.gene_interactions)
        self.mcp_server.tool(name=f"{self.prefix}gene_diseases", description=self.gene_diseases.__doc__)(self.gene_diseases)
        self.mcp_server.tool(name=f"{self.prefix}phenotype_genes", description=self.phenotype_genes.__doc__)(self.phenotype_genes)
        self.mcp_server.tool(name=f"{self.prefix}health_check", description=self.health_check.__doc__)(self.health_check)
