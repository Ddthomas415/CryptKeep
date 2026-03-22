import pytest

from services.security.direct_origin_guard import enforce_direct_origin_block


def test_local_mode_allows_direct_access():
    assert enforce_direct_origin_block(
        auth_scope="local_private_only",
        outer_access_control="",
        headers={},
    ) is True


def test_remote_mode_blocks_without_outer_control():
    with pytest.raises(PermissionError):
        enforce_direct_origin_block(
            auth_scope="remote_public_candidate",
            outer_access_control="",
            headers={},
        )


def test_remote_mode_blocks_direct_origin_without_trusted_header():
    with pytest.raises(PermissionError):
        enforce_direct_origin_block(
            auth_scope="remote_public_candidate",
            outer_access_control="cloudflare_access",
            headers={},
        )


def test_remote_mode_allows_trusted_proxy_header():
    assert enforce_direct_origin_block(
        auth_scope="remote_public_candidate",
        outer_access_control="cloudflare_access",
        headers={"X-Authenticated-Proxy": "1"},
    ) is True

def test_remote_mode_allows_cloudflare_access_header():
    from services.security.direct_origin_guard import enforce_direct_origin_block

    assert enforce_direct_origin_block(
        auth_scope="remote_public_candidate",
        outer_access_control="cloudflare_access",
        headers={"X-Cloudflare-Access": "1"},
    ) is True

def test_remote_mode_allows_cloudflare_access_header():
    from services.security.direct_origin_guard import enforce_direct_origin_block

    assert enforce_direct_origin_block(
        auth_scope="remote_public_candidate",
        outer_access_control="cloudflare_access",
        headers={"X-Cloudflare-Access": "1"},
    ) is True
