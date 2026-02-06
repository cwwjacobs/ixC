"""
API Contract Documentation

This tool depends on UNDOCUMENTED internal ChatGPT endpoints.
These may change without notice.

Last verified: User must verify with `chats-archive verify-api`
"""

API_CONTRACT = {
    "base_url": "https://chatgpt.com/backend-api",
    
    "endpoints": {
        "list_conversations": {
            "method": "GET",
            "path": "/conversations",
            "params": ["offset", "limit"],
            "auth": "Bearer token",
            "returns": {"items": ["conversation metadata"]},
            "status": "ASSUMED"
        },
        "get_conversation": {
            "method": "GET",
            "path": "/conversation/{conversation_id}",
            "auth": "Bearer token",
            "returns": "Full conversation with mapping tree",
            "status": "ASSUMED"
        }
    },
    
    "auth": {
        "type": "Bearer token",
        "source": "Browser session / DevTools",
        "header": "Authorization: Bearer <token>",
        "expiry": "Hours to days (variable)"
    },
    
    "known_responses": {
        200: "Success",
        401: "Token invalid or expired",
        403: "Access forbidden",
        429: "Rate limited",
        404: "Conversation not found or endpoint changed"
    },
    
    "risks": [
        "Endpoints may change without notice",
        "Rate limits are undocumented",
        "Token format may change",
        "API may be deprecated entirely"
    ]
}


def print_contract():
    """Print API contract for user review."""
    import json
    print(json.dumps(API_CONTRACT, indent=2))


if __name__ == "__main__":
    print_contract()
