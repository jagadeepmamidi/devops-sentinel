"""
Supabase setup helpers aligned to the MVP schema.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sentinel.auth.auth_service import get_current_user


SUPABASE_ACCESS_TOKEN = os.environ.get("SUPABASE_ACCESS_TOKEN", "")
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "supabase" / "schema.sql"


class SupabaseSetupRequest(BaseModel):
    project_name: Optional[str] = "devops-sentinel"
    org_id: Optional[str] = None
    region: str = "us-east-1"


class SupabaseSetup:
    MANAGEMENT_API = "https://api.supabase.com/v1"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token or SUPABASE_ACCESS_TOKEN

    def get_setup_sql(self) -> str:
        return SCHEMA_PATH.read_text(encoding="utf-8")

    def get_setup_instructions(self) -> List[Dict]:
        return [
            {
                "step": 1,
                "title": "Create a Supabase project",
                "description": "Open the Supabase dashboard and create a new project.",
                "action_url": "https://supabase.com/dashboard",
            },
            {
                "step": 2,
                "title": "Run the MVP schema",
                "description": "Open SQL Editor and run the schema used by DevOps Sentinel.",
                "sql_path": str(SCHEMA_PATH),
            },
            {
                "step": 3,
                "title": "Copy connection values",
                "description": "Set SUPABASE_URL and SUPABASE_ANON_KEY in your environment.",
            },
            {
                "step": 4,
                "title": "Authenticate with the CLI",
                "description": "Run `sentinel login`, then use `sentinel doctor` to verify auth and API access.",
            },
        ]

    async def verify_connection(self, url: str, key: str) -> Dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url.rstrip('/')}/rest/v1/",
                    headers={"apikey": key, "Authorization": f"Bearer {key}"},
                ) as response:
                    if response.status == 200:
                        return {"connected": True, "message": "Successfully connected"}
                    return {"connected": False, "error": f"Status {response.status}"}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    async def create_project(self, name: str, org_id: str, region: str) -> Dict:
        if not self.access_token:
            raise HTTPException(400, "SUPABASE_ACCESS_TOKEN is required for project creation")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.MANAGEMENT_API}/projects",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": name,
                    "organization_id": org_id,
                    "region": region,
                    "plan": "free",
                },
            ) as response:
                if response.status != 201:
                    raise HTTPException(response.status, await response.text())
                return await response.json()


router = APIRouter(prefix="/api/setup/supabase", tags=["setup"])


@router.get("/instructions")
async def get_setup_instructions():
    setup = SupabaseSetup()
    return {"instructions": setup.get_setup_instructions(), "schema_path": str(SCHEMA_PATH)}


@router.get("/sql")
async def get_setup_sql():
    setup = SupabaseSetup()
    return {"sql": setup.get_setup_sql(), "description": "Run this in the Supabase SQL editor"}


@router.post("/verify")
async def verify_connection(url: str, key: str):
    return await SupabaseSetup().verify_connection(url, key)


@router.post("/create-project")
async def create_project(request: SupabaseSetupRequest, user: Dict = Depends(get_current_user)):
    if not request.org_id:
        return {"error": "Organization ID required"}
    return await SupabaseSetup().create_project(request.project_name, request.org_id, request.region)
