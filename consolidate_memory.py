from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
from memory_state import TravelState
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()


def consolidate_memory(state: TravelState)->None:
    """ 
    Consolidate state.session_memory["notes"] into state.global_memory["notes"].

    - Merges duplicates / near-duplicates
    - Resolves conflicts by keeping most recent (last_update_date)
    - Clears session notes after consolidation
    - Mutates `state` in place
    """
    
    session_notes : List[Dict[str, Any]] = state.session_memory.get("notes", []) or []
    
    
    if not session_notes:
        return 
    
    global_notes: List[Dict[str, Any]] = state.global_memory.get("notes", []) or []
    
    global_json = json.dumps(global_notes, ensure_ascii=False)
    session_json = json.dumps(session_notes, ensure_ascii=False)
    
    consolidation_prompt = f"""
    You are consolidating travel memory notes into LONG-TERM (GLOBAL) memory.

    You will receive two JSON arrays:
    - GLOBAL_NOTES: existing long-term notes
    - SESSION_NOTES: new notes captured during this run

    GOAL
    Produce an updated GLOBAL_NOTES list by merging in SESSION_NOTES.

    RULES
    1) Keep only durable information (preferences, stable constraints, memberships/IDs, long-lived habits).
    2) Drop session-only / ephemeral notes. In particular, DO NOT add a note if it is clearly only for the current trip/session,
    e.g. contains phrases like "this time", "this trip", "for this booking", "right now", "today", "tonight", "tomorrow",
    or describes a one-off circumstance rather than a lasting preference/constraint.
    3) De-duplicate:
    - Remove exact duplicates.
    - Remove near-duplicates (same meaning). Keep a single best canonical version.
    4) Conflict resolution:
    - If two notes conflict, keep the one with the most recent last_update_date (YYYY-MM-DD).
    - If dates tie, prefer SESSION_NOTES over GLOBAL_NOTES.
    5) Note quality:
    - Keep each note short (1 sentence), specific, and durable.
    - Prefer canonical phrasing like: "Prefers aisle seats." / "Avoids red-eye flights." / "Has United Gold status."
    6) Do NOT invent new facts. Only use what appears in the input notes.

    OUTPUT FORMAT (STRICT)
    Return ONLY a valid JSON array.
    Each element MUST be an object with EXACTLY these keys:
    {{"text": string, "last_update_date": "YYYY-MM-DD", "keywords": [string]}}

    Do not include markdown, commentary, code fences, or extra keys.

    GLOBAL_NOTES (JSON):
    <GLOBAL_JSON>
    {global_json}
    </GLOBAL_JSON>

    SESSION_NOTES (JSON):
    <SESSION_JSON>
    {session_json}
    </SESSION_JSON>
    """.strip()
    
    resp = client.responses.create(
        model="gpt-5.2",
        input= consolidation_prompt   
    )
    
    consolidated_text = (resp.output_text or '').strip()
    
    # print(f"Output from model : {consolidated_text}")
    try:
        consolidated_notes = json.loads(consolidated_text)
        print(f"Output after json dumps: {consolidated_text}")
        
        if isinstance(consolidated_notes, list):
            state.global_memory["notes"] = consolidated_notes
        else :
            state.global_memory["notes"] = global_notes + session_notes
    except Exception as error:
        state.global_memory["notes"] = global_notes + session_notes
        
    ## Clear the session memory after consolidation 
    state.session_memory["notes"] = []