"""DevOps Sentinel CLI package.

The lazy export avoids importing the Click application while Python is running
``python -m src.cli.main``.
"""

__all__ = ["cli"]


def __getattr__(name):
    if name == "cli":
        from .main import cli

        return cli
    raise AttributeError(name)
