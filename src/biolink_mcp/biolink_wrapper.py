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
        self.session = aiohttp.ClientSession() = None
    
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
            
    async def get_association(self, params) -> Dict[str, Any]:
        """Retrieve all associations for a given entity, or between two entities"""
        url = f"{self.base_url}/association/"
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
    
    async def get_association(self, subject: str) -> Dict[str, Any]:
        """Fetch an entity by its ID from the Biolink API."""
        return await self.biolink_wrapper.get_entity(subject)
    
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
