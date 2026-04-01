import os
from dotenv import load_dotenv
from gmail_tools import get_gmail_toolkit

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import SystemMessage, HumanMessage, ToolMessage

from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver 

from typing_extensions import Literal


load_dotenv()

toolkit = get_gmail_toolkit()
tools = toolkit.get_tools()
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
checkpointer = InMemorySaver()

# -------------------------------------------------------------------------------------------------------------------------
#
#                                                     SPAM BOT CODE
#
# -------------------------------------------------------------------------------------------------------------------------
def scan_for_spam():
    
    agent = create_agent(model, tools)

    task = {
        "messages": [
            ("system", "You are an expert Email Security AI. Use the gmail tools to fetch and then analyze content."),
            ("user", "Search my Gmail for messages inbox. Analyze the snippets for spam/newsletters and summarize them.")
        ]
    }

    response = agent.invoke(task)
    return response["messages"][-1].content if isinstance(response, dict) else str(response)


# -------------------------------------------------------------------------------------------------------------------------
#
#                                                    MESSAGE SEARCH BOT
#
# -------------------------------------------------------------------------------------------------------------------------
def llm_call(state: MessagesState):
    llm_with_tools = model.bind_tools(tools)
    return {"messages":[llm_with_tools.invoke(state["messages"])]}


def tool_node(state: dict):
    result = []
    observation = tool.invoke(tools)
    result.append(ToolMessage(content=observation, tool_call_id=tools))
    return {"messages": result}


def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"

    return END


def builder_gen():
    builder = StateGraph(MessagesState)
    builder.add_node("llm_call", llm_call)
    builder.add_node("tool_node", tool_node)

    builder.add_edge(START, "llm_call")
    builder.add_conditional_edges(
        "llm_call",
        should_continue,
        ["tool_node", END]
    )
    builder.add_edge("tool_node", "llm_call")
    return builder.compile(checkpointer=checkpointer)


def scan_emails(query: str):
    agent= builder_gen()
    config = {"configurable": {"thread_id": "user_search_session"}}
    input_message = HumanMessage(content=f"Use Gmail tools to search for: {query}")
    
    result = agent.invoke({"messages": [input_message]}, config)
    
    return result["messages"][-1].content
