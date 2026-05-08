"""Service layer for Firecrawl API requests.

This module handles all communication with the Firecrawl API,
keeping authentication and request logic separate from tool definitions.
"""

import logging
from typing import Any, Dict, Optional

import requests
from fastmcp_credentials import get_credentials

from .config import FIRECRAWL_API_BASE, FIRECRAWL_API_VERSION, API_TIMEOUT

logger = logging.getLogger("firecrawl-mcp-server")


def get_headers() -> Dict[str, str]:
    cred = get_credentials()
    token = cred.fields["api_key"]
    if not token:
        raise ValueError(
            "No credential available — ensure X-MCP-Cred-Fields  header is set"
        )
    print("api-key:", token)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def make_firecrawl_request(
    method: str,
    endpoint: str,
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generic request handler for Firecrawl API.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path (e.g., '/scrape')
        body: Optional request body
        params: Optional query parameters

    Returns:
        Response data or error dict
    """
    headers = get_headers()
    url = f"{FIRECRAWL_API_BASE}/{FIRECRAWL_API_VERSION}{endpoint}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body,
            params=params,
            timeout=API_TIMEOUT,
        )
        result = response.json()

        # Successful response (2xx status)
        if 200 <= response.status_code < 300:
            return result

        # Error response
        logger.error(f"Firecrawl API error ({response.status_code}): {result}")
        return {
            "success": False,
            "error": result.get("error", "Unknown error"),
            "statusCode": response.status_code,
            "message": result.get("message", "Firecrawl API request failed"),
            "details": result,
        }

    except requests.exceptions.Timeout:
        error_msg = f"Firecrawl API request timed out after {API_TIMEOUT}s"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "statusCode": 408,
            "message": "Request timeout",
            "details": {},
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"Firecrawl API request failed: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "statusCode": 0,
            "message": "Network error",
            "details": {},
        }

    except Exception as e:
        error_msg = f"Unexpected error in Firecrawl request: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "statusCode": 500,
            "message": "Server error",
            "details": {},
        }
