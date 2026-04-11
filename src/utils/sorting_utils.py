"""Utilities for sorting candidates and profiles."""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def sort_candidates(candidates: List[Any], 
                    priority_order: List[str], 
                    name_key: str = "full_name") -> List[Any]:
    """
    Sort a list of candidates based on a priority order of names.
    
    Args:
        candidates: List of candidate objects (dicts or strings)
        priority_order: List of names in order of preference
        name_key: If candidates are dicts, the key to use for the name
        
    Returns:
        Sorted list of candidates
    """
    if not candidates:
        return []
    
    # Normalize priority order (lowercase and stripped)
    priority_map = {name.lower().strip(): idx for idx, name in enumerate(priority_order)}
    
    def sort_key(candidate):
        name = ""
        if isinstance(candidate, str):
            name = candidate
        elif isinstance(candidate, dict):
            name = str(candidate.get(name_key, ""))
        
        normalized_name = name.lower().strip()
        
        # Match against priority map
        # If not in priority map, they come after prioritized ones, sorted alphabetically
        for priority_name, index in priority_map.items():
            if priority_name in normalized_name:
                return (0, index, normalized_name)
        
        return (1, 0, normalized_name)

    return sorted(candidates, key=sort_key)
