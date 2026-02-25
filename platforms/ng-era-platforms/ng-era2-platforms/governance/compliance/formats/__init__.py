# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Governance Compliance - Formats Module

This module provides GL format layer implementation including
YAML, JSON, K8s, Helm, GitOps, Terraform, OpenAPI, Docker, Markdown, and Rego.
"""

# MNGA-002: Import organization needs review
from .gl_yaml import GLYAML
from .gl_json import GLJSON
from .gl_k8s import GLK8s
from .gl_helm import GLHelm
from .gl_gitops import GLGitOps
from .gl_terraform import GLTerraform
from .gl_openapi import GLOpenAPI
from .gl_docker import GLDocker
from .gl_markdown import GLMarkdown

__all__ = [
    'GLYAML',
    'GLJSON',
    'GLK8s',
    'GLHelm',
    'GLGitOps',
    'GLTerraform',
    'GLOpenAPI',
    'GLDocker',
    'GLMarkdown'
]

__version__ = '1.0.0'