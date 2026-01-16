import os
import sys
import asyncio
from agents import Agent, Runner, RunConfig, ModelSettings, set_tracing_disabled, RunContextWrapper
from context_management import TrimmingSession
from memory_hooks import render_frontmatter, render_global_memories_md, render_session_memories_md, MemoryHooks
from memory_distillation import save_memory_note
from context_management import TrimmingSession
from memory_state import MemoryNote, TravelState, user_state
from dotenv import load_dotenv
from consolidate_memory import consolidate_memory

load_dotenv()

session = TrimmingSession("first_session", user_state, max_turns=1)

set_tracing_disabled(True)

MEMORY_INSTRUCTIONS = """
<memory_policy>
You may receive two memory lists:
- GLOBAL memory = long-term defaults (“usually / in general”).
- SESSION memory = trip-specific overrides (“this trip / this time”).

How to use memory:
- Use memory only when it is relevant to the user’s current decision (flight/hotel/insurance choices).
- Apply relevant memory automatically when setting tone, proposing options and making recommendations.
- Do not repeat memory verbatim to the user unless it’s necessary to confirm a critical constraint.

Precedence and conflicts:
1) The user’s latest message in this conversation overrides everything.
2) SESSION memory overrides GLOBAL memory for this trip when they conflict.
   - Example: GLOBAL “usually aisle” + SESSION “this time window to sleep” ⇒ choose window for this trip.
3) Within the same memory list, if two items conflict, prefer the most recent by date.
4) Treat GLOBAL memory as a default, not a hard constraint, unless the user explicitly states it as non-negotiable.

When to ask a clarifying question:
- Ask exactly one focused question only if a memory materially affects booking and the user’s intent is ambiguous.
  (e.g., “Do you want to keep the window seat preference for all legs or just the overnight flight?”)

Where memory should influence decisions (check these before suggesting options):
- Flights: seat preference, baggage habits (carry-on vs checked), airline loyalty/status, layover tolerance if mentioned.
- Hotels: neighborhood/location style (central/walkable), room preferences (high floor), brand loyalty IDs/status.
- Insurance: known coverage profile (e.g., CDW included) and whether the user wants add-ons this trip.

Memory updates:
- Do NOT treat “this time” requests as changes to GLOBAL defaults.
- Only promote a preference into GLOBAL memory if the user indicates it’s a lasting rule
  (e.g., “from now on”, “generally”, “I usually prefer X now”).
- If a new durable preference/constraint appears, store it via the memory tool (short, general, non-PII).

Safety:
- Never store or echo sensitive PII (passport numbers, payment details, full DOB).
- If a memory seems stale or conflicts with user intent, defer to the user and proceed accordingly.
</memory_policy>
"""


BASE_INSTRUCTIONS = f"""
You are a concise, reliable travel concierge. 
Help users plan and book flights, hotels, and car/travel insurance.\n\n

Guidelines:\n
- Collect key trip details and confirm understanding.\n
- Ask only one focused clarifying question at a time.\n
- Provide a few strong options with brief tradeoffs, then recommend one.\n
- Respect stable user preferences and constraints; avoid assumptions.\n
- Before booking, restate all details and get explicit approval.\n
- Never invent prices, availability, or policies—use tools or state uncertainty.\n
- Do not repeat sensitive PII; only request what is required.\n
- Track multi-step itineraries and unresolved decisions.\n\n
"""

async def instructions(ctx: RunContextWrapper[TravelState], agent:Agent) -> str:
    s = ctx.context
    
    # print(f"inject_session_memories_next_turn: {s.inject_session_memories_next_turn}")
    # print(f"session_memories_md: {s.session_memories_md}")
    
    # if s.inject_session_memories_next_turn and not s.session_memories_md:
    #     s.session_memories_md = render_session_memories_md(
    #         (s.session_memory or {}).get("notes", [])
    #     )
    #     print(f"session memory markdown: {s.session_memories_md}")
        
    session_block = ""
    
    if s.session_memory and s.session_memory.get("notes", False) and not s.session_memories_md:
        s.session_memories_md = render_session_memories_md(s.session_memory.get("notes",[]))
        
        session_block = (
            "\n\nSESSION memory (temporary; overrides Global when conflicting):\n"
            + s.session_memories_md
        )
        
        s.session_memories_md = ""
    
    if s.session_memories_md:
        session_block = (
            "\n\nSESSION memory (temporary; overrides Global when conflicting):\n"
            + s.session_memories_md
        )
        
        s.session_memories_md = ""
    
        if s.inject_session_memories_next_turn:
            s.inject_session_memories_next_turn = False
    
    # print(f"session block: {session_block}")
    
    return (
        BASE_INSTRUCTIONS 
        + "\n\n<user_profile>\n" + (s.system_frontmatter or "") +"\n</user_profile>"
        + "\n\n<memories>\n"
        + "GLOBAL memory: \n" + (s.global_memories_md or "- (none)")
        + session_block
        + "\n</memories>"
        + "\n\n" + MEMORY_INSTRUCTIONS
    )
    
    
async def main():
    
    travel_concierge_agent = Agent(
        name = "Travel Concierge",
        model = "gpt-5.2",
        instructions=instructions,
        hooks=MemoryHooks(),
        tools= [save_memory_note]
    )
    
    r1 = await Runner.run(
        travel_concierge_agent,
        input = "Book me a flight to paris next month.",
        session=session,
        context= user_state,
    )
    
    # print("Turn 1:", r1.final_output)
    
    r2 = await Runner.run(
        travel_concierge_agent,
        input = "Do you know my preferences??",
        session=session,
        context= user_state,
    )
    # print("Turn 2:", r2.final_output)
    
    
    r3 = await Runner.run(
        travel_concierge_agent,
        input = "Remember that i am vegetarian.",
        session=session,
        context= user_state,
    )
    # print("Turn 3:", r3.final_output)
    
    
    # print(f"Session memory: {user_state.session_memory}")
    
    r4 = await Runner.run(
        travel_concierge_agent,
        input = "This time, I like to have a window seat. i really want to sleep",
        session=session,
        context= user_state,
    )
    
    # print("\nTurn 4: ", r4.final_output)
    
    # print(f"lets see session memory again: {user_state.session_memory}")
    
    # ### 
    # print("\nUser session memory \n\n")
    # print(user_state.session_memory)
    
    # ## 
    # print("\nGlobal memory\n\n")
    # print(user_state.global_memory)
    
    # consolidate_memory(user_state)
    
    # print("\n\n After updating the global memory.")
    
    # print("\nUser session memory \n\n")
    # print(user_state.session_memory)
    
    # ## 
    # print("\nGlobal memory\n\n")
    # print(user_state.global_memory)
    
    
    
if __name__ == "__main__":
    asyncio.run(main())