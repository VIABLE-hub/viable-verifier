"""
Path utilities for cross-platform path resolution.

This module provides utilities to resolve paths relative to the project root,
ensuring cross-platform compatibility (macOS, Linux, Windows).
"""

import os
from pathlib import Path
from typing import Optional

# Cache for project root to avoid repeated lookups
_project_root: Optional[Path] = None


def get_project_root() -> Path:
    """
    Get the project root directory by looking for marker files.
    
    The project root is identified by the presence of one of these files:
    - README.md
    - Makefile
    - viable-credentials.jsonl
    
    Returns:
        Path: Absolute path to the project root directory
        
    Raises:
        RuntimeError: If project root cannot be determined
    """
    global _project_root
    
    # Return cached value if available
    if _project_root is not None:
        return _project_root
    
    # Start from the current file and walk up
    current_path = Path(__file__).resolve()
    
    # Marker files that indicate the project root (must be at root, not in backend/)
    markers = ['README.md', 'Makefile', 'viable-credentials.jsonl']
    
    # Walk up the directory tree
    for parent in list(current_path.parents):
        # Skip if this directory is named 'backend' - project root should be above it
        if parent.name == 'backend':
            continue
            
        # Check if any marker file exists in this directory
        for marker in markers:
            if (parent / marker).exists():
                # Verify this is actually the project root by checking for backend/ subdirectory
                if (parent / 'backend').is_dir():
                    _project_root = parent
                    return _project_root
    
    # Fallback: if we're in backend/src, go up to find project root
    # The path structure is: project_root/backend/src/path_utils.py
    # So we need to go up 2 levels from src to get to project root
    if 'backend' in current_path.parts and 'src' in current_path.parts:
        # Find the backend directory
        parts_list = list(current_path.parts)
        backend_idx = parts_list.index('backend')
        # Project root is the parent of backend directory
        # So we take everything up to (but not including) backend, then go up one more
        if backend_idx > 0:
            # We're at: /project/backend/src/file.py
            # We want: /project
            # So we take parts up to backend_idx, which gives us /project/backend
            # Then we need the parent of that
            backend_path = Path(*parts_list[:backend_idx + 1])
            _project_root = backend_path.parent
        else:
            # If backend is at the start, we need to go up from current_path
            # Count how many levels up from backend/src
            src_idx = parts_list.index('src')
            levels_up = len(parts_list) - src_idx - 1  # Levels from src to project root
            _project_root = current_path.parents[levels_up]
        return _project_root
    
    # Last resort: use current working directory
    # This assumes the app is run from the project root
    _project_root = Path.cwd()
    return _project_root


def get_backend_path(*path_parts: str) -> Path:
    """
    Get a path relative to the backend directory.
    
    Args:
        *path_parts: Path components relative to backend directory
        
    Returns:
        Path: Absolute path to the requested location
        
    Example:
        get_backend_path('instance', 'keys') -> /project/backend/instance/keys
    """
    project_root = get_project_root()
    return project_root / 'backend' / Path(*path_parts)


def get_instance_path(*path_parts: str) -> Path:
    """
    Get a path relative to the backend/instance directory.
    
    Args:
        *path_parts: Path components relative to backend/instance directory
        
    Returns:
        Path: Absolute path to the requested location
        
    Example:
        get_instance_path('keys') -> /project/backend/instance/keys
    """
    return get_backend_path('instance', *path_parts)

