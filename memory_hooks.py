from agents import AgentHooks, Agent, RunContextWrapper, RunConfig
from memory_distillation import TravelState, user_state
from context_management import TrimmingSession
from agents.items import TResponseInputItem
import yaml
from typing import Optional

def render_frontmatter(profile:dict) -> str:
    playload = {"profile": profile}
    y = yaml.safe_dump(playload, sort_keys=False).strip()
    return f"---\n{y}\n---"

def render_global_memories_md(global_notes: list[dict], k:int = 6) -> str:
    if not global_notes:
        return "- {None}"
    
    notes_sorted = sorted(global_notes, key=lambda n: n.get("last_update_date", ""), reverse=True)
    top = notes_sorted[:k]
    return "\n".join([f"- {n["text"]}" for n in top])

def render_session_memories_md(session_notes: list[dict], k:int = 8) -> str:
    if not session_notes:
        return "- (None)"
    
    ## keeps most recent notes; 
    top = session_notes[-k:]
    return "\n".join(f"- {n['text']}" for n in top)



class MemoryHooks(AgentHooks[TravelState]):
    # def __init__(self, client: client) -> None:
    #     self.client = client
    
    async def on_start(self, ctx: RunContextWrapper[TravelState], agent:Agent) -> None:
        ctx.context.system_frontmatter = render_frontmatter(ctx.context.profile)
        ctx.context.global_memories_md = render_global_memories_md((ctx.context.global_memory or {}).get("notes", []))

        session_notes = (ctx.context.session_memory or {}).get("notes", [])
        
        if session_notes:
            ctx.context.session_memories_md = render_session_memories_md(
                session_notes
            )

        if ctx.context.inject_session_memories_next_turn:
            ctx.context.inject_session_memories_next_turn = False
            
    async def on_llm_start(
        self,
        context: RunContextWrapper,
        agent: Agent,
        system_prompt: Optional[str],
        input_items: list[TResponseInputItem],
    ) -> None:
        """Called immediately before the agent issues an LLM call."""
        print(f"\n\n System Prompt: \n {system_prompt}")
        # pass