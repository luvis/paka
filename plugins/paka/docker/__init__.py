"""
Docker Plugin for PAKA

A package manager plugin that treats Docker containers as packages.
"""

from .docker_manager import DockerPackageManager

__all__ = ['DockerPackageManager'] 