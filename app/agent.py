from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.services import calendar_svc

class AgentState(TypedDict):
    phone_number: str
    messages: list
    stage: str
    calendar_checked: bool
    proposed_time: str
    is_confirmed: bool
    api_key: str
    system_prompt: str

def qualification_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    api_key = state.get("api_key")
    system_prompt = state.get("system_prompt", "You are an AI appointment setter for a home services company. Does the user want to schedule? Respond YES or NO.")
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)
    sys_msg = SystemMessage(content=system_prompt + " Does the user want to schedule? Respond YES or NO.")
    response = llm.invoke([sys_msg, HumanMessage(content=last_msg)])
    
    if "YES" in response.content.upper():
        state["stage"] = "rules_check"
    else:
        state["stage"] = "answering_questions"
    return state

def rules_node(state: AgentState) -> AgentState:
    state["stage"] = "calendar_check"
    return state

def calendar_node(state: AgentState) -> AgentState:
    availability = calendar_svc.get_availability()
    state["calendar_checked"] = True
    if availability:
        state["proposed_time"] = availability[0]
        state["stage"] = "confirmation"
    else:
        state["proposed_time"] = ""
        state["stage"] = "no_availability"
    return state

def confirmation_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1].content
    if "yes" in last_msg.lower() or "sure" in last_msg.lower() or "ok" in last_msg.lower():
        state["is_confirmed"] = True
        state["stage"] = "booked"
    return state

def generate_response_node(state: AgentState) -> dict:
    stage = state["stage"]
    if stage == "answering_questions":
        reply = "I'd be happy to answer your questions. We handle residential cleaning in your area. Would you like to check availability?"
    elif stage == "rules_check":
        reply = "Great! Let me check if we service your zip code."
    elif stage == "calendar_check" or stage == "confirmation":
        if state.get("is_confirmed"):
            reply = f"Perfect! You are booked for {state['proposed_time']}."
        else:
            reply = f"I have an opening at {state['proposed_time']}. Does that work for you?"
    else:
        reply = "Let me know how I can help!"
    return {"reply": reply, "state": state}

workflow = StateGraph(AgentState)
workflow.add_node("qualify", qualification_node)
workflow.add_node("rules", rules_node)
workflow.add_node("calendar", calendar_node)
workflow.add_node("confirm", confirmation_node)

workflow.add_conditional_edges("qualify", lambda state: state["stage"], {"rules_check": "rules", "answering_questions": END})
workflow.add_edge("rules", "calendar")
workflow.add_conditional_edges("calendar", lambda state: state["stage"], {"confirmation": "confirm", "no_availability": END})
workflow.add_edge("confirm", END)
workflow.set_entry_point("qualify")

app_graph = workflow.compile()

def process_message(phone: str, user_message: str, api_key: str, system_prompt: str, current_state: dict = None) -> tuple[str, dict]:
    if current_state is None:
        state = AgentState(
            phone_number=phone,
            messages=[HumanMessage(content=user_message)],
            stage="new",
            calendar_checked=False,
            proposed_time="",
            is_confirmed=False,
            api_key=api_key,
            system_prompt=system_prompt
        )
    else:
        state = current_state
        state["messages"].append(HumanMessage(content=user_message))
        state["api_key"] = api_key
        state["system_prompt"] = system_prompt
        
    new_state = app_graph.invoke(state)
    res = generate_response_node(new_state)
    return res["reply"], res["state"]
