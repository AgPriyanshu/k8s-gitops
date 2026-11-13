import operator
from typing import Annotated

from langchain_openai import ChatOpenAI
from langgraph.graph.state import StateGraph
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate

class State(BaseModel):
    messages: Annotated[list[BaseMessage], operator.add]

graph = StateGraph(State)

class Task(BaseModel):
    prompt: str | None
    is_llm_based: bool 
    is_parallel: bool 

class PlannerOutput(BaseModel):
    subTasks: list[Task]


planner_prompt = PromptTemplate.from_template("""
    You are a planner expert. Divide the user query into tasks 
    Query - {user_prompt}
    Structure to return - 
      subTasks: [{
        prompt: str -> Prompt for LLM task
        is_llm_based: bool -> for identifying if it is an llm task
        is_parallel: bool -> can this task be executed parallely
    }]
    reply in the structured output
""")
def planner(state):    
    llm = ChatOpenAI(
        model="qwen/qwen3.5-9b",
        base_url="http://localhost:1234/v1",
        api_key="lm-studio",  
        reasoning={
            "effort": "none",
        },
    )   
    latest_message = state.messages[-1]
    result = llm.with_structured_output(PlannerOutput).invoke(planner_prompt.format(user_prompt=latest_message))

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
print(agent.invoke(State(messages=[HumanMessage(content=""" I want to build an AI-powered customer support platform for SaaS companies.

Research the top 5 competitors in this space, compare their features, pricing, target audience, and weaknesses. Identify the most promising market gap we can exploit.

Meanwhile, research the best LLM models for customer support automation, compare OpenAI, Anthropic, and open-source alternatives in terms of cost, latency, accuracy, and deployment complexity.

Design a scalable backend architecture using Python, FastAPI, PostgreSQL, Redis, and RabbitMQ. The platform should support multi-tenancy, streaming responses, human handoff, conversation history, and integrations with Slack and WhatsApp.

Also investigate the security and compliance requirements for handling customer conversations, including GDPR and SOC 2.

Finally, prepare a product roadmap for the first 3 months, including MVP features, development milestones, estimated infrastructure costs, and a recommended technology stack.

Combine everything into a comprehensive technical and business proposal.""")]))   )

async def trigger_llm_pipeline(message: str):
    return await agent.invoke(State(messages=[HumanMessage(content="message")]))    