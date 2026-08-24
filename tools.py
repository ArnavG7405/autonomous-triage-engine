# tools.py
import re

def check_database(message: str) -> str:
    """Simulates an API call to a SQL customer database to check account status."""
    msg_lower = message.lower()
    
    # Simulate DB lookup for billing issues
    if any(w in msg_lower for w in ["charge", "billing", "$", "payment"]):
        if "twice" in msg_lower or "duplicate" in msg_lower:
            return "DATABASE_LOOKUP: Account Flagged - 2 identical Stripe charges pending in last 24h."
        if "$1,200" in msg_lower:
            return "DATABASE_LOOKUP: Subscription Status - Starter. No Enterprise plan active (Possible Fraud)."
            
    # Simulate DB lookup for account access
    if "locked" in msg_lower or "password" in msg_lower:
        return "DATABASE_LOOKUP: Account Status - Locked (Max password attempts exceeded)."
        
    return ""

def search_knowledge_base(message: str) -> str:
    """Simulates a RAG vector search over internal engineering runbooks."""
    msg_lower = message.lower()
    
    if "500 error" in msg_lower or "api" in msg_lower:
        return "RAG_SEARCH: Runbook Match -> '500 Errors on /v1/checkout' = Known Redis latency issue (Active P0 Incident)."
        
    if "csv" in msg_lower and "export" in msg_lower:
        return "RAG_SEARCH: Runbook Match -> 'CSV Export Bug' = Known frontend React unmount issue with date filters. Fix in v2.4 (P2 Priority)."
        
    return ""