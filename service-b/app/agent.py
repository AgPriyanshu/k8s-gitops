import operator
from typing import Annotated

from langchain_openai import ChatOpenAI
from langgraph.graph.state import StateGraph
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

class State(BaseModel):
    messages: Annotated[list[BaseMessage], operator.add]

graph = StateGraph(State)


def planner(state):
    llm = ChatOpenAI(
        model="qwen/qwen3.5-9b",
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",  
    )   
    latest_message = state.messages[-1]
    result = llm.invoke(latest_message.content)

    return {"messages": [result]}

def executor(state):
    return {"messages": [HumanMessage("message from executor")]}

# Nodes.
graph.add_node("planner",planner)
graph.add_node("executor",executor)

# Edges.
graph.add_edge("planner","executor")

# Set entry and exit points.
graph.set_entry_point("planner")
graph.set_finish_point("executor")

# Compile.
agent = graph.compile()
print(agent.invoke(State(messages=[HumanMessage(content="tell me about life")]))   )

async def trigger_llm_pipeline():
    return await agent.invoke(State(messages=[HumanMessage(content="do something")]))    