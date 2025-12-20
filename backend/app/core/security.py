"""
Security utilities for Alpha Machine.
Optional API authentication can be added here.
"""
from typing import Optional
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key validation.
    Returns None if no API key is configured or provided.
    """
    return api_key
