"""The agent: a LangGraph loop   START -> agent -> tools -> agent -> ... -> END.

Usage (runs one trial on one task, in a temporary copy of the repo):
    python agent.py 01_paginate A
"""

import shutil
import sys
import tempfile
import json

from pathlib import Path
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from prompts import PROMPTS
from tools import make_tools

MODEL = "qwen2.5:14b"
MAX_STEPS = 10  # max number of LLM calls per trial
BENCHMARK_DIR = Path(__file__).resolve().parent / "benchmark"



class AgentState(TypedDict):
    # The whole conversation. `add_messages` means: when a node returns
    # {"messages": [...]}, the new messages are APPENDED, not replacing the list.
    messages: Annotated[list[AnyMessage], add_messages]
    # Number of LLM calls so far. No annotation: a returned value REPLACES the old one.
    steps: int

def parse_text_tool_calls(message, tool_names):
    """Find tool calls written as JSON text, e.g. {"name": "run_tests", "arguments": {}}."""
    decoder = json.JSONDecoder()
    i = str.find(message, "{")
    calls = []
    while i >= 0:
        try:  
            obj, end = decoder.raw_decode(message, i)
        except json.JSONDecodeError:
            i = str.find(message, "{", i+1)
            continue
        if isinstance(obj, dict) and obj.get("name") in tool_names and  isinstance(obj.get("arguments", {}), dict):
            calls.append({"name": obj.get("name"), "args": obj.get("arguments", {}), "id": f"text_call_{len(calls)}"})
        i = message.find("{", end)
    return calls
    

def build_agent(tools, system_prompt, model=MODEL, temperature=0.7, num_predict=1000):
    """Build and compile the graph for one trial."""
    llm = ChatOllama(model=model, temperature=temperature, num_predict=num_predict).bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}

    def call_model(state: AgentState):
        """Node "agent": ask the LLM what to do next."""
        message = llm.invoke([SystemMessage(system_prompt)] + state["messages"])
        if message.tool_calls == []:
            calls = parse_text_tool_calls(message.content, tools_by_name)
            if (calls != []):
                message.tool_calls = calls
            
        return {"messages": [message], "steps": state["steps"]+1}

    def call_tools(state: AgentState):
        """Node "tools": run every tool call requested in the last LLM message."""
        last_message = state["messages"][-1]
        tool_messages = []
        for call in last_message.tool_calls:
            try :
                tool = tools_by_name[call["name"]]
                try: 
                    result = tool.invoke(call["args"])
                except Exception as e:
                    result = "Arguments created an exception, you should verify them" + " here is the execption : " + str(e)
            except Exception as e:
                result = "The tool doesn't exist, here is the list of tools : " + (", ".join(tools_by_name.keys())) + " here is the exception : " + str(e)
            
            tool_messages.append(ToolMessage(content=result, tool_call_id=call["id"]))
        
        return {"messages": tool_messages}
            
    def route(state: AgentState):
        """Conditional edge after "agent": where do we go next?"""
        last_message = state["messages"][-1]
        if (state["steps"] < MAX_STEPS and last_message.tool_calls) : 
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", call_tools)
    graph.add_edge(START, "agent")
    graph.add_edge("tools", "agent")
    graph.add_conditional_edges("agent", route)
    return graph.compile()


def build_task_message(task_dir, repo_dir):
    """First user message: the issue, plus the list of files so the model knows what exists."""
    issue = (task_dir / "ISSUE.md").read_text()
    files = sorted(p.name for p in repo_dir.iterdir() if p.suffix == ".py")
    return f"Issue:\n{issue}\nFiles in the repository: {', '.join(files)}"


if __name__ == "__main__":
    task_name = sys.argv[1] if len(sys.argv) > 1 else "01_paginate"
    variant = sys.argv[2] if len(sys.argv) > 2 else "A"
    task_dir = BENCHMARK_DIR / task_name

    # Work on a temporary copy: the original repo is never modified.
    with tempfile.TemporaryDirectory() as tmp:
        repo_dir = Path(tmp) / "repo"
        shutil.copytree(task_dir / "repo", repo_dir)

        agent = build_agent(make_tools(repo_dir), PROMPTS[variant])
        initial_state = {"messages": [HumanMessage(build_task_message(task_dir, repo_dir))], "steps": 0}
        # recursion_limit is LangGraph's own safety net (counts every node run);
        # our real limit is MAX_STEPS, so we just set it high enough.
        final_state = agent.invoke(initial_state, {"recursion_limit": 50})

        for message in final_state["messages"]:
            message.pretty_print()
        print(f"\nLLM calls: {final_state['steps']}")
