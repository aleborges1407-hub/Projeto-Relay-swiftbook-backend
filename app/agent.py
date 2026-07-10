from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

class AgentState(TypedDict):
    phone_number: str
    messages: list
    api_key: str
    ai_config: dict
    reply: str

def build_system_prompt(ai_config: dict) -> str:
    if not ai_config:
        return "Você é um assistente virtual prestativo."
    
    prompt = f"Você é a assistente virtual da empresa {ai_config.get('company_name', 'Nossa Empresa')}.\n"
    if ai_config.get('business_type'):
        prompt += f"Segmento: {ai_config.get('business_type')}.\n"
    if ai_config.get('tone'):
        prompt += f"Tom de voz: {ai_config.get('tone')}.\n"
    if ai_config.get('base_prompt'):
        prompt += f"Objetivo principal: {ai_config.get('base_prompt')}.\n"
    if ai_config.get('business_rules'):
        prompt += f"Regras de negócio: {ai_config.get('business_rules')}.\n"
    if ai_config.get('products_services'):
        prompt += f"Produtos/Serviços: {ai_config.get('products_services')}.\n"
    if ai_config.get('faq'):
        prompt += f"FAQ: {ai_config.get('faq')}.\n"
        
    prompt += "\nInstruções:\n- Seja conciso e direto, ideal para WhatsApp.\n- Baseie-se apenas nas regras e informações fornecidas.\n- Mantenha o contexto das mensagens anteriores."
    return prompt

def conversational_node(state: AgentState) -> AgentState:
    api_key = state.get("api_key")
    ai_config = state.get("ai_config", {})
    messages = state.get("messages", [])
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)
    
    system_prompt_text = build_system_prompt(ai_config)
    sys_msg = SystemMessage(content=system_prompt_text)
    
    llm_messages = [sys_msg] + messages
    response = llm.invoke(llm_messages)
    
    state["reply"] = response.content
    return state

workflow = StateGraph(AgentState)
workflow.add_node("conversation", conversational_node)
workflow.set_entry_point("conversation")
workflow.add_edge("conversation", END)
app_graph = workflow.compile()

def process_message(phone: str, user_message: str, api_key: str, ai_config: dict, current_state: dict = None, memory_messages: list = None) -> tuple[str, dict]:
    if memory_messages is None:
        memory_messages = []
        
    messages = memory_messages.copy()
    messages.append(HumanMessage(content=user_message))

    if current_state is None:
        state = AgentState(
            phone_number=phone,
            messages=messages,
            api_key=api_key,
            ai_config=ai_config,
            reply=""
        )
    else:
        state = current_state
        state["messages"] = messages
        state["api_key"] = api_key
        state["ai_config"] = ai_config
        
    new_state = app_graph.invoke(state)
    return new_state["reply"], new_state
