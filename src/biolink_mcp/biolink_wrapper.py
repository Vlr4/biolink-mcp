#!/usr/bin/env python3
"""Biolink API tools for MCP server."""

import logging
import aiohttp
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

# Setup logger for this module
logger = logging.getLogger(__name__)

class BiolinkAPIWrapper:
    """Wrapper for the Biolink API. Currently implements Get Entity and Search """
    
    def __init__(self, base_url: str = "https://api-v3.monarchinitiative.org/v3/api"):
        self.base_url = base_url
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Return an existing session or create a new one."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close the session."""
        if self.session and not self.session.closed:
            await self.session.close()
               
    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Fetch a bioentity by its ID."""
        url = f"{self.base_url}/entity/{entity_id}"
        session = await self._get_session()
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()
            
    async def get_association(
        self,
        entity_id: str,
        category: str,
        path: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Retrieve association table data for a given entity and association type.

        Args:
            entity_id: e.g. "MONDO:0019391"
            category: e.g. "biolink:DiseaseToPhenotypicFeatureAssociation"
            path: optional path string to restrict results to a subset
            offset: pagination offset
            limit: pagination limit
        """
        # URL-encode id & category (colons must be encoded)
        id_enc = quote(entity_id, safe="")
        cat_enc = quote(category, safe="")
        url = f"{self.base_url}/entity/{id_enc}/{cat_enc}"

        params = {"offset": offset, "limit": limit}
        if path:
            params["path"] = path

        session = await self._get_session()
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def search(self, params) -> Dict[str, Any]:
        """Search for bioentities by label"""
        url = f"{self.base_url}/search"
        session = await self._get_session()
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()
    
    async def normalize_id(self, query: str, taxon: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Normalize a biological term and return its canonical ID, full name, and category"""
        params = {"q": query}
        if taxon:
            params["in_taxon_label"] = taxon
        url = f"{self.base_url}/search"
        session = await self._get_session()
        async with session.get(url, params=params) as response:
            if response.status != 200:
                return {"id": None, "full_name": None, "category": None}
            data = await response.json()
            items = data.get("items", [])
            if not items:
                return {"id": None, "full_name": None, "category": None}
            top = items[0]
            return {
                "id": top.get("id"),
                "full_name": top.get("full_name"),
                "category": top.get("category")
                }

class BiolinkTools:
    """Handler for Biolink API-related MCP tools."""
    
    def __init__(self, mcp_server, prefix: str = ""):
        self.mcp_server = mcp_server
        self.prefix = prefix
        self.biolink_wrapper = BiolinkAPIWrapper()
    
    async def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """Fetch an entity by its ID from the Biolink API."""
        return await self.biolink_wrapper.get_entity(entity_id)
    
    async def get_association(
        self,
        entity_id: str,
        category: str,
        path: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Retrieve association table data for an entity and association category."""
        return await self.biolink_wrapper.get_association(
            entity_id=entity_id, category=category, path=path, offset=offset, limit=limit
        )
    
    async def search(self, q: str) -> Dict[str, Any]:
        """Search for entities in the Biolink API."""
        return await self.biolink_wrapper.search(q)
    
    async def normalize_id(self, query: str, taxon: Optional[str] = None) -> Dict[str, Optional[str]]:
        """Normalize a biological term and return its canonical ID, full name, and category. Optional: restrict by taxon label."""
        return await self.biolink_wrapper.normalize_id(query, taxon)

    
    def register_tools(self):
        """Register Biolink-related MCP tools."""
        self.mcp_server.tool(
            name=f"{self.prefix}get_entity",
            description=self.get_entity.__doc__
        )(self.get_entity)

        self.mcp_server.tool(
            name=f"{self.prefix}get_association",
            description=self.get_association.__doc__
        )(self.get_association)
        
        self.mcp_server.tool(
            name=f"{self.prefix}search",
            description=self.search.__doc__
        )(self.search)

        self.mcp_server.tool(
            name=f"{self.prefix}normalize",
            description=self.normalize_id.__doc__
        )(self.normalize_id)
