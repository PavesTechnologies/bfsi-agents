"""
CLI entrypoint for local development.
"""

import uvicorn


def dev():
    uvicorn.run("src.main:app", reload=True, port=8004, reload_dirs=["src"])


def prod():
    uvicorn.run(
        "src.main:app",
        port=8004,
    )


def test():
    print("Running tests...")
    import pytest

    pytest.main(["-v", "tests/"])

    print("Tests complete.")
