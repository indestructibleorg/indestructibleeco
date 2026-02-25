# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Governance Compliance - Languages Module

This module provides GL language layer implementation including
Python, Go, TypeScript, Rust, Java, C#, SQL, and Shell naming conventions.
"""

from .gl_python import GLPythonNaming
from .gl_go import GLGoNaming
from .gl_typescript import GLTypeScriptNaming
from .gl_rust import GLRustNaming
from .gl_java import GLJavaNaming
from .gl_csharp import GLCSharpNaming
from .gl_sql import GLSQLNaming
from .gl_shell import GLShellNaming

__all__ = [
    'GLPythonNaming',
    'GLGoNaming',
    'GLTypeScriptNaming',
    'GLRustNaming',
    'GLJavaNaming',
    'GLCSharpNaming',
    'GLSQLNaming',
    'GLShellNaming'
]

__version__ = '1.0.0'