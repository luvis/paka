#!/usr/bin/env python3
"""
Health Management Module

This module provides backward compatibility by importing from the new
modular health management structure.
"""

from .health.base import HealthCheck, HealthManager

__all__ = ['HealthCheck', 'HealthManager'] 