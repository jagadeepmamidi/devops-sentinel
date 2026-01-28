"""
Waitlist API Endpoint
=====================

Handle waitlist signups with email validation and duplicate prevention
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
import re


router = APIRouter(tags=["waitlist"])


class WaitlistSignup(BaseModel):
    """Waitlist signup request"""
    email: EmailStr
    referrer: Optional[str] = None
    source: Optional[str] = None  # 'homepage', 'producthunt', 'twitter', etc.
    
    @validator('email')
    def validate_business_email(cls, v):
        """Prefer business emails, but allow personal"""
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = v.split('@')[1].lower()
        
        # Just log, don't reject personal emails
        if domain in personal_domains:
            # Could add a flag for follow-up priority
            pass
        
        return v.lower()


class WaitlistResponse(BaseModel):
    """Waitlist signup response"""
    success: bool
    message: str
    position: Optional[int] = None
    already_registered: bool = False


# In-memory storage for demo (use Supabase in production)
waitlist_db = []


@router.post("/api/waitlist", response_model=WaitlistResponse)
async def join_waitlist(signup: WaitlistSignup):
    """
    Join the early access waitlist
    
    - Validates email
    - Prevents duplicates
    - Returns waitlist position
    """
    email = signup.email.lower()
    
    # Check for duplicate
    for entry in waitlist_db:
        if entry['email'] == email:
            return WaitlistResponse(
                success=True,
                message="You're already on the waitlist!",
                position=entry['position'],
                already_registered=True
            )
    
    # Add to waitlist
    position = len(waitlist_db) + 1
    
    waitlist_db.append({
        'email': email,
        'position': position,
        'referrer': signup.referrer,
        'source': signup.source,
        'signed_up_at': datetime.utcnow().isoformat()
    })
    
    # In production: Send confirmation email, notify admin
    
    return WaitlistResponse(
        success=True,
        message="Welcome to the waitlist!",
        position=position,
        already_registered=False
    )


@router.get("/api/waitlist/count")
async def get_waitlist_count():
    """Get current waitlist count (for social proof)"""
    return {
        'count': len(waitlist_db),
        'milestone': (len(waitlist_db) // 100 + 1) * 100  # Next milestone
    }


@router.get("/api/waitlist/position/{email}")
async def get_waitlist_position(email: str):
    """Check waitlist position by email"""
    email = email.lower()
    
    for entry in waitlist_db:
        if entry['email'] == email:
            return {
                'found': True,
                'position': entry['position'],
                'signed_up_at': entry['signed_up_at']
            }
    
    return {'found': False}


# Admin endpoints (would require auth in production)

@router.get("/api/admin/waitlist")
async def get_all_waitlist():
    """Admin: Get all waitlist entries"""
    return {
        'total': len(waitlist_db),
        'entries': waitlist_db,
        'by_source': _get_source_breakdown()
    }


def _get_source_breakdown():
    """Get breakdown of signups by source"""
    sources = {}
    for entry in waitlist_db:
        source = entry.get('source', 'direct')
        sources[source] = sources.get(source, 0) + 1
    return sources


# Demo data for testing
if __name__ == "__main__":
    import asyncio
    
    async def demo():
        # Simulate signups
        result = await join_waitlist(WaitlistSignup(
            email="test@example.com",
            source="homepage"
        ))
        print(f"Signup 1: Position {result.position}")
        
        result = await join_waitlist(WaitlistSignup(
            email="devops@company.io",
            source="twitter"
        ))
        print(f"Signup 2: Position {result.position}")
        
        # Try duplicate
        result = await join_waitlist(WaitlistSignup(
            email="test@example.com"
        ))
        print(f"Duplicate: Already registered = {result.already_registered}")
        
        # Get count
        count = await get_waitlist_count()
        print(f"Total waitlist: {count['count']}")
    
    asyncio.run(demo())
