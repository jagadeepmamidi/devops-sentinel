"""
Supabase Quick Setup - One-Click Database
==========================================

Helps users set up Supabase with one click:
1. Creates project via API (if they have org access token)
2. Or guides them through manual setup with auto-detection
"""

import os
from typing import Dict, List, Optional
from datetime import datetime

import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.auth.auth_service import get_current_user


# Supabase Management API
SUPABASE_ACCESS_TOKEN = os.environ.get('SUPABASE_ACCESS_TOKEN', '')


class SupabaseSetupRequest(BaseModel):
    """Request to create/configure Supabase project"""
    project_name: Optional[str] = "devops-sentinel"
    org_id: Optional[str] = None
    region: str = "us-east-1"


class SupabaseSetup:
    """
    Supabase Setup Helper
    
    Two modes:
    1. Auto: User provides Supabase access token → We create project
    2. Guided: We give step-by-step instructions with auto-detection
    """
    
    MANAGEMENT_API = "https://api.supabase.com/v1"
    
    # Required tables for DevOps Sentinel
    REQUIRED_TABLES = [
        {
            'name': 'users',
            'sql': '''
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    subscription_tier TEXT DEFAULT 'byok',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            '''
        },
        {
            'name': 'services',
            'sql': '''
                CREATE TABLE IF NOT EXISTS services (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    name TEXT NOT NULL,
                    url TEXT,
                    health_check_url TEXT,
                    status TEXT DEFAULT 'unknown',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            '''
        },
        {
            'name': 'incidents',
            'sql': '''
                CREATE TABLE IF NOT EXISTS incidents (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    service_id UUID REFERENCES services(id),
                    title TEXT NOT NULL,
                    description TEXT,
                    severity TEXT DEFAULT 'P2',
                    status TEXT DEFAULT 'open',
                    detected_at TIMESTAMPTZ DEFAULT NOW(),
                    resolved_at TIMESTAMPTZ,
                    resolution TEXT,
                    embedding VECTOR(1536)
                );
            '''
        },
        {
            'name': 'slack_integrations',
            'sql': '''
                CREATE TABLE IF NOT EXISTS slack_integrations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    team_id TEXT NOT NULL,
                    team_name TEXT,
                    bot_token TEXT,
                    webhook_url TEXT,
                    webhook_channel TEXT,
                    installed_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(user_id, team_id)
                );
            '''
        },
        {
            'name': 'github_integrations',
            'sql': '''
                CREATE TABLE IF NOT EXISTS github_integrations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) UNIQUE,
                    github_user_id TEXT,
                    github_username TEXT,
                    access_token TEXT,
                    installed_at TIMESTAMPTZ DEFAULT NOW()
                );
            '''
        }
    ]
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token or SUPABASE_ACCESS_TOKEN
    
    async def create_project(self, name: str, org_id: str, region: str) -> Dict:
        """Create a new Supabase project"""
        if not self.access_token:
            raise HTTPException(
                400, 
                "Supabase access token required. Get it from supabase.com/dashboard/account/tokens"
            )
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.MANAGEMENT_API}/projects",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'name': name,
                    'organization_id': org_id,
                    'region': region,
                    'plan': 'free'
                }
            ) as resp:
                if resp.status != 201:
                    error = await resp.text()
                    raise HTTPException(resp.status, f"Failed to create project: {error}")
                
                return await resp.json()
    
    def get_setup_sql(self) -> str:
        """Get SQL to set up all required tables"""
        # Enable vector extension first
        sql = "-- Enable pgvector for incident memory\n"
        sql += "CREATE EXTENSION IF NOT EXISTS vector;\n\n"
        
        for table in self.REQUIRED_TABLES:
            sql += f"-- {table['name']} table\n"
            sql += table['sql'] + "\n\n"
        
        # Add RLS policies
        sql += """
-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE slack_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_integrations ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can view own services" ON services
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own incidents" ON incidents
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own integrations" ON slack_integrations
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage GitHub integration" ON github_integrations
    FOR ALL USING (auth.uid() = user_id);
"""
        return sql
    
    def get_setup_instructions(self) -> List[Dict]:
        """Get step-by-step setup instructions"""
        return [
            {
                'step': 1,
                'title': 'Create Supabase Account',
                'description': 'Go to supabase.com and sign up for free',
                'action_url': 'https://supabase.com/dashboard',
                'action_text': 'Open Supabase'
            },
            {
                'step': 2,
                'title': 'Create New Project',
                'description': 'Click "New Project", choose a name and region',
                'tip': 'Use a strong database password - save it somewhere safe!'
            },
            {
                'step': 3,
                'title': 'Run Setup SQL',
                'description': 'Go to SQL Editor and run this script',
                'sql': self.get_setup_sql(),
                'action_text': 'Copy SQL'
            },
            {
                'step': 4,
                'title': 'Copy Your Keys',
                'description': 'Go to Settings > API and copy your keys',
                'keys': [
                    {'name': 'Project URL', 'env': 'SUPABASE_URL'},
                    {'name': 'anon/public key', 'env': 'SUPABASE_ANON_KEY'}
                ]
            },
            {
                'step': 5,
                'title': 'Done!',
                'description': 'Paste the keys in your .env file and restart the app'
            }
        ]
    
    async def verify_connection(self, url: str, key: str) -> Dict:
        """Verify Supabase connection works"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{url}/rest/v1/",
                    headers={
                        'apikey': key,
                        'Authorization': f'Bearer {key}'
                    }
                ) as resp:
                    if resp.status == 200:
                        return {'connected': True, 'message': 'Successfully connected!'}
                    else:
                        return {'connected': False, 'error': f'Status {resp.status}'}
        except Exception as e:
            return {'connected': False, 'error': str(e)}


# FastAPI Router
router = APIRouter(prefix="/api/setup/supabase", tags=["setup"])


@router.get("/instructions")
async def get_setup_instructions():
    """Get step-by-step Supabase setup instructions"""
    setup = SupabaseSetup()
    return {
        "instructions": setup.get_setup_instructions(),
        "estimated_time": "5 minutes"
    }


@router.get("/sql")
async def get_setup_sql():
    """Get SQL to set up database tables"""
    setup = SupabaseSetup()
    return {
        "sql": setup.get_setup_sql(),
        "description": "Run this in Supabase SQL Editor"
    }


@router.post("/verify")
async def verify_connection(url: str, key: str):
    """Verify Supabase connection"""
    setup = SupabaseSetup()
    return await setup.verify_connection(url, key)


@router.post("/create-project")
async def create_project(
    request: SupabaseSetupRequest,
    user: Dict = Depends(get_current_user)
):
    """Create a new Supabase project (requires access token)"""
    setup = SupabaseSetup()
    
    if not request.org_id:
        return {
            "error": "Organization ID required",
            "help": "Get your org ID from supabase.com/dashboard/org/_/settings"
        }
    
    return await setup.create_project(
        request.project_name,
        request.org_id,
        request.region
    )
