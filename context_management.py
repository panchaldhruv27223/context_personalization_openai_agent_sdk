from __future__ import annotations
import asyncio
from collections import deque
from typing import Any, Deque, List, Dict, cast
from agents.memory.session import SessionABC
from agents.items import TResponseInputItem
from memory_state import TravelState, user_state

ROLE_USER = "user"

def _is_user_msg(item:TResponseInputItem) -> bool:
    """
    Return True if the item represents a user message.
    """
    
    if isinstance(item, dict):
        role = item.get("role")
        
        if role is not None:
            return role == ROLE_USER
        
        if item.get("type") == "message":
            return item.get("role") == ROLE_USER
        
    return getattr(item, "role", None) == ROLE_USER


class TrimmingSession(SessionABC):
    """Keep only the last N "User turn" in memory.
    
    A Turn = a user message and all subsequent items (assistant/ tool call / results) up to (but not including) the next user message."""
    
    def __init__(self, session_id: str, state: TravelState, max_turns: int=8) -> None:
        super().__init__()
        self.session_id = session_id
        self.state = state
        self.max_turns  = max(1,max_turns)
        self._items : Deque[TResponseInputItem] = deque()  ## Chronological log
        self._lock = asyncio.Lock()
        
    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        """Return history trimmed to the last N user turns (Optionally limited to most-recent `limit` items)."""
        async with self._lock:
            trimmed = self._trim_to_last_turns(list(self._items))
            return trimmed[-limit:] if (limit is not None and limit>=0) else trimmed
        
    async def add_items(self, items: List[TResponseInputItem]) -> None:
        """Append new items, then trim to last N user turns."""
        
        if not items:
            return 
        
        async with self._lock:
            self._items.extend(items)
            
            original_len = len(self._items)
            trimmed = self._trim_to_last_turns(list(self._items))
            
            if len(trimmed) < original_len:
                # Flag for triggering session injection after context trimming
                self.state.inject_session_memories_next_turn = True
            self._items.clear()
            self._items.extend(trimmed)
            
    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item (post-trim)."""
        
        async with self._lock:
            return self._items.pop() if self._items else None
        
    async def clear_session(self) -> None:
        """Remove all items for this session."""
        async with self._lock:
            self._items.clear()
            
            
    #### lets define the helper function
    # ---Helpers---
    
    def _trim_to_last_turns(self, items: List[TResponseInputItem]) -> List[TResponseInputItem]:
        """
        Keep only the suffix containing the last 'max_turns' user messages and everything afetr the earliest of those user messages.
        if there are fewer than 'max_tuns' user messages (or none), keep all itmes.
        """
        
        if not items:
            return items
        
        count = 0 
        start_idx = 0 #### default : keep all if we never reach max_turns
        
        # walk backward; when we hit the Nth user message, mark its index.
        
        for i in range(len(items)-1, -1, -1):
            if _is_user_msg(items[i]):
                count += 1
                if count == self.max_turns:
                    start_idx = i
                    break
                
        return items[start_idx:]
    
    
    #### --- optional convenience api ---
    
    async def set_max_turns(self, max_turns:int)->None:
        async with self._lock:
            self.max_turns = max(1, max_turns)
            trimmed = self._trim_to_last_turns(list(self._items))
            self._items.clear()
            self._items.extend(trimmed)

    async def raw_items(self) -> List[TResponseInputItem]:
        """Return The untrimmed in-memory log(for debugging)."""
        async with self._lock:
            return list(self._items)
