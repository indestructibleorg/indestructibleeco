# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Governance Compliance - Platforms Module

This module provides GL platform layer implementation including
platforms, components, services, modules, packages, resources,
events, APIs, environments, labels, and file system management.
"""

from .gl_platform import GLPlatform
from .gl_component import GLComponent
from .gl_service import GLService, GLAPIEndpoint
from .gl_module import GLModule
from .gl_package import GLPackage
from .gl_resource import GLResource
from .gl_event import GLEvent
from .gl_environment import GLEnvironment
from .gl_label import GLLabel
from .gl_comment import GLComment
from .gl_filesystem import GLFileSystem

__all__ = [
    'GLPlatform',
    'GLComponent',
    'GLService',
    'GLAPIEndpoint',
    'GLModule',
    'GLPackage',
    'GLResource',
    'GLEvent',
    'GLEnvironment',
    'GLLabel',
    'GLComment',
    'GLFileSystem'
]

__version__ = '1.0.0'