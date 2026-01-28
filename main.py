"""
DevOps Sentinel
===============
Autonomous SRE Agent System

Usage:
    python main.py                  Show help
    python main.py serve            Start dashboard server
    python main.py monitor <url>    Monitor a service

For CLI usage:
    sentinel init                   Setup configuration
    sentinel monitor <url>          Monitor a service
    sentinel serve                  Start dashboard server
"""

from cli import main

if __name__ == "__main__":
    main()