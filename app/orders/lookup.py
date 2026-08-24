import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Path to the orders dataset
ORDERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "orders.json"
)

_orders_cache: Dict[str, Any] = {}
_snapshot_time: Optional[datetime] = None

def load_dataset() -> Dict[str, Any]:
    global _orders_cache, _snapshot_time
    if _orders_cache:
        return _orders_cache
        
    if not os.path.exists(ORDERS_FILE):
        raise FileNotFoundError(f"Orders file not found at {ORDERS_FILE}")
        
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    _orders_cache = {order["order_id"].upper(): order for order in data["orders"]}
    
    # Parse snapshot_at
    snapshot_str = data.get("snapshot_at", "2026-08-15T12:00:00Z")
    # Handle 'Z' for UTC python < 3.11 compatibility if needed, but python 3.11+ supports it or we can replace it
    if snapshot_str.endswith("Z"):
        snapshot_str = snapshot_str[:-1] + "+00:00"
    _snapshot_time = datetime.fromisoformat(snapshot_str)
    
    return data

def get_snapshot_time() -> datetime:
    load_dataset()
    return _snapshot_time or datetime.now(timezone.utc)

def extract_order_id(text: str) -> Optional[str]:
    """
    Extracts an order ID from text.
    Matches ORD-XXXX, ord-XXXX, ORD XXXX, ord XXXX, ordXXXX, etc.
    """
    if not text:
        return None
    match = re.search(r'\b(ord)[-\s]*(\d+)\b', text, re.IGNORECASE)
    if match:
        num = match.group(2)
        return f"ORD-{num}"
    return None

def lookup_order(order_id: str) -> Dict[str, Any]:
    """
    Looks up an order by ID. Normalizes whitespace, lowercase, etc.
    Returns customer-safe fields only, with status-precedence logic applied.
    """
    load_dataset()
    
    # Normalize ID
    normalized_id = order_id.strip().upper()
    # Normalize cases like ORD1007 to ORD-1007 if missing hyphen
    if normalized_id.startswith("ORD") and "-" not in normalized_id:
        normalized_id = f"ORD-{normalized_id[3:]}"
        
    if normalized_id not in _orders_cache:
        return {
            "found": False,
            "order_id": normalized_id,
            "error_message": f"Order {normalized_id} not found."
        }
        
    order = _orders_cache[normalized_id]
    status = order.get("status")
    
    # Calculate time since placed (using snapshot time as current time)
    placed_at_str = order.get("placed_at", "")
    if placed_at_str.endswith("Z"):
        placed_at_str = placed_at_str[:-1] + "+00:00"
    placed_at = datetime.fromisoformat(placed_at_str)
    
    time_diff = get_snapshot_time() - placed_at
    minutes_since_placed = time_diff.total_seconds() / 60.0
    cancellation_allowed = (status == "pending" and minutes_since_placed <= 30.0)
    address_change_allowed = (status == "pending" and minutes_since_placed <= 30.0)
    
    # Filter customer-safe fields
    # Customer-safe fields: order_id, membership_tier, items.name/quantity/final_sale, placed_at, status, status_updated_at, shipped_at, delivered_at, carrier, tracking_number, estimated_delivery, customer_safe_message
    items = []
    for item in order.get("items", []):
        items.append({
            "name": item.get("name"),
            "quantity": item.get("quantity"),
            "final_sale": item.get("final_sale", False)
        })
        
    # Build clean output dictionary
    result = {
        "found": True,
        "order_id": order.get("order_id"),
        "membership_tier": order.get("membership_tier"),
        "items": items,
        "placed_at": order.get("placed_at"),
        "status": status,
        "status_updated_at": order.get("status_updated_at"),
        "customer_safe_message": order.get("customer_safe_message"),
        "cancellation_allowed": cancellation_allowed,
        "address_change_allowed": address_change_allowed,
        "minutes_since_placed": round(minutes_since_placed, 1)
    }
    
    # Status Precedence Rules:
    # 1. When status is cancelled or returned, clear stale delivery fields.
    if status in ["cancelled", "returned"]:
        result["estimated_delivery"] = None
        result["carrier"] = None
        result["tracking_number"] = None
        result["shipped_at"] = None
        result["delivered_at"] = None
    else:
        # Include fields if not cancelled/returned
        result["shipped_at"] = order.get("shipped_at")
        result["delivered_at"] = order.get("delivered_at")
        result["carrier"] = order.get("carrier")
        result["tracking_number"] = order.get("tracking_number")
        
        # 2. When status is shipped but estimated_delivery is null, report unavailable.
        # 3. Avoid inventing a delivery estimate when one is unavailable.
        result["estimated_delivery"] = order.get("estimated_delivery")
        
    return result
