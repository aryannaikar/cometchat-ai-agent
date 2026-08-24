from app.orders.lookup import extract_order_id, lookup_order

def test_extract_order_id():
    assert extract_order_id("Where is my order ORD-1007?") == "ORD-1007"
    assert extract_order_id("Where is my order ord-1007?") == "ORD-1007"
    assert extract_order_id("track ord 1007 please") == "ORD-1007"
    assert extract_order_id("ord1007 status") == "ORD-1007"
    assert extract_order_id("No order id here") is None

def test_lookup_order_success():
    res = lookup_order("ORD-1007")
    assert res["found"] is True
    assert res["order_id"] == "ORD-1007"
    assert res["membership_tier"] == "standard"
    assert "customer" not in res
    assert "internal" not in res
    assert res["status"] == "shipped"

def test_lookup_order_normalization():
    res = lookup_order("  ord-1007  ")
    assert res["found"] is True
    assert res["order_id"] == "ORD-1007"
    
    res2 = lookup_order("ord1007")
    assert res2["found"] is True
    assert res2["order_id"] == "ORD-1007"

def test_lookup_order_not_found():
    res = lookup_order("ORD-9999")
    assert res["found"] is False
    assert "error_message" in res

def test_cancelled_order_stale_fields():
    # ORD-1004 is cancelled in orders.json and has carrier, tracking, estimated_delivery
    res = lookup_order("ORD-1004")
    assert res["status"] == "cancelled"
    assert res["estimated_delivery"] is None
    assert res["carrier"] is None
    assert res["tracking_number"] is None
