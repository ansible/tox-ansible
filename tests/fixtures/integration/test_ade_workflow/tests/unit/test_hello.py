"""Minimal unit test for the hello module."""

from __future__ import annotations


def test_hello_documentation():
    """Verify the hello module has DOCUMENTATION defined."""
    from ansible_collections.test_ns.test_col.plugins.modules import hello

    assert hasattr(hello, "DOCUMENTATION")
    assert "hello" in hello.DOCUMENTATION
