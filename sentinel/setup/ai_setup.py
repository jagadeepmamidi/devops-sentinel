"""
OpenAI/OpenRouter Quick Setup
==============================

Helps users get AI keys with guidance
"""

import os
from typing import Dict, List
import aiohttp
from fastapi import APIRouter


class AIProviderSetup:
    """
    AI Provider Setup Helper
    
    Supports:
    - OpenAI (best quality)
    - OpenRouter (cheaper, multiple providers)
    - Anthropic (Claude)
    """
    
    PROVIDERS = {
        'openai': {
            'name': 'OpenAI',
            'description': 'Best quality for postmortems and embeddings',
            'signup_url': 'https://platform.openai.com/signup',
            'api_keys_url': 'https://platform.openai.com/api-keys',
            'pricing': 'Pay as you go (~$0.002 per postmortem)',
            'env_key': 'OPENAI_API_KEY',
            'models': ['gpt-4o', 'gpt-4o-mini', 'text-embedding-3-small']
        },
        'openrouter': {
            'name': 'OpenRouter',
            'description': 'Access multiple AI providers, often cheaper',
            'signup_url': 'https://openrouter.ai/auth',
            'api_keys_url': 'https://openrouter.ai/keys',
            'pricing': 'Pay as you go (varies by model)',
            'env_key': 'OPENROUTER_API_KEY',
            'models': ['openai/gpt-4o', 'anthropic/claude-3-haiku', 'google/gemini-pro']
        },
        'anthropic': {
            'name': 'Anthropic (Claude)',
            'description': 'Great for detailed analysis',
            'signup_url': 'https://console.anthropic.com/signup',
            'api_keys_url': 'https://console.anthropic.com/settings/keys',
            'pricing': 'Pay as you go',
            'env_key': 'ANTHROPIC_API_KEY',
            'models': ['claude-3-5-sonnet', 'claude-3-haiku']
        }
    }
    
    def get_provider_options(self) -> List[Dict]:
        """Get all provider options"""
        return [
            {
                'id': key,
                **info,
                'recommended': key == 'openrouter'  # Cheaper for most users
            }
            for key, info in self.PROVIDERS.items()
        ]
    
    def get_setup_instructions(self, provider: str) -> List[Dict]:
        """Get setup instructions for a specific provider"""
        info = self.PROVIDERS.get(provider)
        if not info:
            return []
        
        return [
            {
                'step': 1,
                'title': f'Create {info["name"]} Account',
                'description': 'Sign up for a free account',
                'action_url': info['signup_url'],
                'action_text': f'Sign up for {info["name"]}'
            },
            {
                'step': 2,
                'title': 'Create API Key',
                'description': 'Generate a new API key',
                'action_url': info['api_keys_url'],
                'action_text': 'Create API Key'
            },
            {
                'step': 3,
                'title': 'Add to Your Environment',
                'description': f'Add this to your .env file:',
                'code': f'{info["env_key"]}=sk-your-api-key-here'
            },
            {
                'step': 4,
                'title': 'Done!',
                'description': 'Restart the app to activate AI features',
                'pricing_note': info['pricing']
            }
        ]
    
    async def verify_key(self, provider: str, api_key: str) -> Dict:
        """Verify an API key works"""
        if provider == 'openai':
            return await self._verify_openai(api_key)
        elif provider == 'openrouter':
            return await self._verify_openrouter(api_key)
        elif provider == 'anthropic':
            return await self._verify_anthropic(api_key)
        return {'valid': False, 'error': 'Unknown provider'}
    
    async def _verify_openai(self, api_key: str) -> Dict:
        """Verify OpenAI key"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {api_key}'}
                ) as resp:
                    if resp.status == 200:
                        return {'valid': True, 'message': 'OpenAI key verified!'}
                    return {'valid': False, 'error': 'Invalid API key'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    async def _verify_openrouter(self, api_key: str) -> Dict:
        """Verify OpenRouter key"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://openrouter.ai/api/v1/models',
                    headers={'Authorization': f'Bearer {api_key}'}
                ) as resp:
                    if resp.status == 200:
                        return {'valid': True, 'message': 'OpenRouter key verified!'}
                    return {'valid': False, 'error': 'Invalid API key'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    async def _verify_anthropic(self, api_key: str) -> Dict:
        """Verify Anthropic key"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://api.anthropic.com/v1/messages',
                    headers={
                        'x-api-key': api_key,
                        'anthropic-version': '2023-06-01',
                        'content-type': 'application/json'
                    },
                    json={
                        'model': 'claude-3-haiku-20240307',
                        'max_tokens': 1,
                        'messages': [{'role': 'user', 'content': 'Hi'}]
                    }
                ) as resp:
                    if resp.status in [200, 400]:  # 400 = valid key, bad request
                        return {'valid': True, 'message': 'Anthropic key verified!'}
                    return {'valid': False, 'error': 'Invalid API key'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}


# FastAPI Router
router = APIRouter(prefix="/api/setup/ai", tags=["setup"])


@router.get("/providers")
async def list_providers():
    """List available AI providers"""
    setup = AIProviderSetup()
    return {"providers": setup.get_provider_options()}


@router.get("/instructions/{provider}")
async def get_instructions(provider: str):
    """Get setup instructions for a provider"""
    setup = AIProviderSetup()
    instructions = setup.get_setup_instructions(provider)
    if not instructions:
        return {"error": "Unknown provider"}
    return {"instructions": instructions}


@router.post("/verify")
async def verify_key(provider: str, api_key: str):
    """Verify an API key"""
    setup = AIProviderSetup()
    return await setup.verify_key(provider, api_key)
