from app.rag.authority import AuthorityResolver


def test_current_policy_is_authoritative():
    resolver = AuthorityResolver()

    current = {
        "metadata": {
            "document_id": "RET-2026-01",
            "filename": "01-returns-policy-current.md",
            "status": "active",
            "policy_authority": "official",
            "audience": "customer",
        }
    }

    result = resolver.resolve(current)

    assert result.status == "authoritative"


def test_superseded_45_day_policy_is_not_authoritative():
    resolver = AuthorityResolver()

    legacy = {
        "metadata": {
            "document_id": "RET-2024-01",
            "filename": "02-returns-policy-legacy.md",
            "status": "superseded",
            "policy_authority": "official",
            "audience": "customer",
            "superseded_by": "RET-2026-01",
        }
    }

    result = resolver.resolve(legacy)

    assert result.status == "superseded"


def test_current_policy_outranks_superseded_policy():
    resolver = AuthorityResolver()

    current = {
        "metadata": {
            "document_id": "RET-2026-01",
            "status": "active",
            "policy_authority": "official",
            "audience": "customer",
        }
    }

    legacy = {
        "metadata": {
            "document_id": "RET-2024-01",
            "status": "superseded",
            "policy_authority": "official",
            "audience": "customer",
        }
    }

    current_result = resolver.resolve(current)
    legacy_result = resolver.resolve(legacy)

    assert (
        current_result.authority_score
        > legacy_result.authority_score
    )


def test_draft_internal_document_is_not_authoritative():
    resolver = AuthorityResolver()

    migration = {
        "metadata": {
            "document_id": "MIG-TEST-04",
            "status": "draft",
            "audience": "internal",
            "policy_authority": "none",
            "customer_answering": False,
        }
    }

    result = resolver.resolve(migration)

    assert result.status == "non_authoritative"
    assert result.authority_score < 0