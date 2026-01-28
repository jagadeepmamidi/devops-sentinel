"""
BYOK (Bring Your Own Key) Tier Helper
======================================

Detects if user has provided their own API keys
and automatically assigns them the 'byok' tier.
"""

import os
from typing import Dict, Optional


class BYOKDetector:
    """
    Detect if user is BYOK (Bring Your Own Key)
    
    BYOK users get UNLIMITED access because:
    - They pay OpenAI/Supabase directly
    - We just provide the platform
    - No cost to us = no limits needed
    
    Tier Assignment:
    - Has own OpenAI/Supabase keys → 'byok' (unlimited)
    - No keys, just browsing → 'free' (demo limits)
    - Paid for our managed keys → 'pro' or 'enterprise'
    """
    
    # Required keys for full BYOK status
    BYOK_REQUIRED_KEYS = [
        'OPENAI_API_KEY',      # Or OPENROUTER_API_KEY
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY'
    ]
    
    # Alternative keys that also count
    ALTERNATIVE_KEYS = {
        'OPENAI_API_KEY': ['OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY']
    }
    
    @classmethod
    def is_byok_environment(cls) -> bool:
        """
        Check if the current environment has user-provided keys
        
        Returns:
            True if user has provided their own API keys
        """
        for key in cls.BYOK_REQUIRED_KEYS:
            # Check main key
            if os.environ.get(key):
                continue
            
            # Check alternatives
            alternatives = cls.ALTERNATIVE_KEYS.get(key, [])
            if not any(os.environ.get(alt) for alt in alternatives):
                return False
        
        return True
    
    @classmethod
    def get_tier_for_environment(cls) -> str:
        """
        Determine tier based on environment configuration
        
        Returns:
            'byok' if user has own keys, 'free' otherwise
        """
        # Check for managed tier override (paid users)
        managed_tier = os.environ.get('MANAGED_TIER')
        if managed_tier in ['pro', 'enterprise']:
            return managed_tier
        
        # Check for BYOK
        if cls.is_byok_environment():
            return 'byok'
        
        return 'free'
    
    @classmethod
    def get_tier_for_user(cls, user: Optional[Dict]) -> str:
        """
        Determine tier for a specific user
        
        Priority:
        1. User's subscription_tier (if paid)
        2. BYOK detection (if has keys)
        3. Free tier (default)
        """
        if user:
            user_tier = user.get('tier') or user.get('subscription_tier')
            
            # Paid tiers take priority
            if user_tier in ['pro', 'enterprise']:
                return user_tier
            
            # Check if BYOK
            if cls.is_byok_environment():
                return 'byok'
            
            return user_tier or 'free'
        
        # No user, check environment
        return cls.get_tier_for_environment()
    
    @classmethod
    def get_available_features(cls, tier: str) -> Dict[str, bool]:
        """
        Get feature availability for a tier
        
        Returns dict of feature_name -> is_available
        """
        features = {
            # Core features - available to all
            'health_checks': True,
            'basic_monitoring': True,
            'incident_tracking': True,
            
            # AI features - require OpenAI key
            'ai_postmortems': tier in ['byok', 'pro', 'enterprise'],
            'incident_memory': tier in ['byok', 'pro', 'enterprise'],
            'smart_suggestions': tier in ['byok', 'pro', 'enterprise'],
            
            # Advanced features
            'slack_integration': True,  # Uses their own Slack
            'unlimited_services': tier in ['byok', 'pro', 'enterprise'],
            'team_collaboration': tier in ['byok', 'pro', 'enterprise'],
            'sla_tracking': tier in ['pro', 'enterprise'],
            
            # Enterprise only
            'dedicated_support': tier == 'enterprise',
            'custom_integrations': tier == 'enterprise',
            'sso': tier == 'enterprise'
        }
        
        return features
    
    @classmethod
    def get_missing_keys(cls) -> list:
        """
        Get list of missing API keys for BYOK
        
        Returns:
            List of missing key names
        """
        missing = []
        
        for key in cls.BYOK_REQUIRED_KEYS:
            if os.environ.get(key):
                continue
            
            # Check alternatives
            alternatives = cls.ALTERNATIVE_KEYS.get(key, [])
            if not any(os.environ.get(alt) for alt in alternatives):
                missing.append(key)
        
        return missing


def get_user_tier(user: Optional[Dict] = None) -> str:
    """Convenience function to get tier for current user"""
    return BYOKDetector.get_tier_for_user(user)


def is_feature_available(feature: str, user: Optional[Dict] = None) -> bool:
    """Check if a feature is available for user"""
    tier = get_user_tier(user)
    features = BYOKDetector.get_available_features(tier)
    return features.get(feature, False)
