"""DevOps Sentinel CLI package."""

__all__ = ["cli"]


def __getattr__(name):
    if name == "cli":
        from .main import cli

        return cli
    raise AttributeError(name)
