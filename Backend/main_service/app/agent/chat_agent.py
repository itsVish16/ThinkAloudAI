from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from app.config import settings
import datetime
import os

@tool
def get_current_time() -> str:
    """Returns the current date and time. Use this tool whenever the user asks for the current date or time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def web_search(query: str) -> str:
    """Search the web for information regarding the query. 
    Uses Tavily API to fetch the most relevant and recent information."""
    api_key = os.environ.get("TAVILY_API_KEY") or settings.TAVILY_API_KEY
    if not api_key:
        return "[Error] TAVILY_API_KEY is not configured in the environment."
        
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="basic", include_answer=True)
        
        results_str = f"Search Answer: {response.get('answer', 'No direct answer found.')}\n\nSources:\n"
        for idx, result in enumerate(response.get("results", [])[:3]):
            results_str += f"{idx+1}. {result.get('title')} ({result.get('url')})\n   {result.get('content')}\n"
            
        return results_str
    except Exception as e:
        return f"[Error] Web search failed: {str(e)}"

from app.database import SessionLocal
from app.models.dsa import DSAQuestion, CodeSubmission
from app.models.roadmap import Roadmap, RoadmapTopic, RoadmapItem
from typing import Optional
import json

from sqlalchemy.future import select

@tool
async def get_dsa_questions(question_id: Optional[int] = None) -> str:
    """Use this tool to fetch DSA questions from the database. 
    If question_id is provided, returns details of that specific question (including description and test cases).
    If question_id is None, returns a list of all available questions (IDs and Titles)."""
    async with SessionLocal() as db:
        try:
            if question_id:
                result = await db.execute(select(DSAQuestion).filter(DSAQuestion.id == question_id))
                q = result.scalars().first()
                if q:
                    return f"Title: {q.title}\nDifficulty: {q.difficulty}\nFunction Name: {q.function_name}\nDescription: {q.description}\nTest Cases: {q.test_cases}"
                return "Question not found."
            else:
                result = await db.execute(select(DSAQuestion))
                qs = result.scalars().all()
                if not qs:
                    return "No questions available."
                res = "Available DSA Questions:\n"
                for q in qs:
                    res += f"- ID: {q.id}, Title: {q.title}, Difficulty: {q.difficulty}\n"
                return res
        except Exception as e:
            return f"Error fetching questions: {str(e)}"

@tool
async def get_user_submissions(session_id: str) -> str:
    """Use this tool to fetch the user's latest code submissions to see what code they have written and why it might have failed.
    Pass the user's current session_id."""
    async with SessionLocal() as db:
        try:
            result = await db.execute(select(CodeSubmission).filter(CodeSubmission.session_id == session_id).order_by(CodeSubmission.created_at.desc()).limit(5))
            subs = result.scalars().all()
            if not subs:
                return "No submissions found for this session."
            res = "User's Recent Submissions:\n\n"
            for s in subs:
                res += f"Question ID: {s.question_id}\nLanguage: {s.language}\nStatus: {s.status}\nError: {s.error_message}\nCode:\n```\n{s.code}\n```\n---\n"
            return res
        except Exception as e:
            return f"Error fetching submissions: {str(e)}"

@tool
async def create_user_roadmap(title: str, description: str, topics: str) -> str:
    """Use this tool to generate a detailed, multi-topic learning roadmap for the user based on their needs.
    'title' is the roadmap title. 'description' is a short summary.
    'topics' MUST be a JSON-encoded string representing a list of topics.
    Example topics format:
    [
      {
        "title": "Week 1: Arrays & Interviews",
        "order_index": 0,
        "items": [
          {"title": "Two Sum", "content_type": "dsa", "content_id": "1", "timeline_days": 1},
          {"title": "Array Basics Mock Interview", "content_type": "mock_interview", "content_id": "dsa", "timeline_days": 1},
          {"title": "Read about HashMaps", "content_type": "custom", "content_id": null, "timeline_days": 2}
        ]
      }
    ]
    """
    async with SessionLocal() as db:
        try:
            if isinstance(topics, str):
                topics_data = json.loads(topics)
            else:
                topics_data = topics
            
            roadmap = Roadmap(
                user_id="test_user_id", # Hardcoded for now to match API route
                title=title,
                description=description
            )
            db.add(roadmap)
            await db.flush()
            
            for topic_data in topics_data:
                topic = RoadmapTopic(
                    roadmap_id=roadmap.id,
                    title=topic_data.get("title", "Topic"),
                    order_index=topic_data.get("order_index", 0)
                )
                db.add(topic)
                await db.flush()
                
                for item_data in topic_data.get("items", []):
                    item = RoadmapItem(
                        topic_id=topic.id,
                        title=item_data.get("title", "Item"),
                        content_type=item_data.get("content_type", "custom"),
                        content_id=str(item_data.get("content_id")) if item_data.get("content_id") else None,
                        timeline_days=item_data.get("timeline_days", None),
                        is_completed=False
                    )
                    db.add(item)
                    
            await db.commit()
            return f"Successfully created roadmap '{title}' with ID {roadmap.id}."
        except Exception as e:
            await db.rollback()
            return f"Error creating roadmap: {e}"

tools = [get_current_time, web_search, get_dsa_questions, get_user_submissions, create_user_roadmap]

# Initialize LLM using Featherless base URL and API key
llm = ChatOpenAI(
    model=os.environ.get("FEATHERLESS_MODEL", "meta-llama/Meta-Llama-3-70B-Instruct"),
    base_url="https://api.featherless.ai/v1",
    api_key=os.environ.get("FEATHERLESS_API_KEY"),
    max_tokens=2048,
    temperature=0.4
)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

# Define the system prompt
system_prompt = (
    "You are an expert Data Structures and Algorithms (DSA) Interviewer and coding mentor at ThinkAloud.ai. "
    "Your goal is to conduct realistic coding interviews, evaluate the user's code, and guide them without giving away the direct answers immediately.\n\n"
    "Guidelines:\n"
    "1. When the user asks for a question, use 'get_dsa_questions' to find an appropriate problem, and present it clearly.\n"
    "2. If the user submits code or asks 'why did my code fail?', use 'get_user_submissions' with their session_id to read exactly what they wrote and what errors occurred.\n"
    "3. Do not just fix the code for them. Point out the specific line or logical error and ask them how they might resolve it.\n"
    "4. For System Design, follow a structured framework (Requirements gathering, API design, High-Level Design, bottlenecks).\n"
    "5. Be encouraging, professional, and precise. Use markdown formatting to make your answers structured and readable.\n"
    "6. You have real-time tools: 'get_current_time', 'web_search', 'get_dsa_questions', 'get_user_submissions', and 'create_user_roadmap'.\n"
    "7. If the user asks for a study plan or roadmap, use the 'create_user_roadmap' tool to generate a structured timeline for them.\n"
    "8. IMPORTANT: If the user asks to 'schedule an interview' or 'set up a mock interview' (e.g. for Arrays), DO NOT conduct the interview in text. Instead, use the 'create_user_roadmap' tool to create a single-item roadmap with content_type='mock_interview' and content_id matching their requested topic (e.g., 'dsa' or specific question IDs like '1,2'). This will spawn a real WebRTC video interview for them!\n"
    "9. Before providing your final answer to the user, you MUST ALWAYS think step-by-step and place all your internal reasoning inside <think> ... </think> tags. Once you close the </think> tag, output your final response."
)

# Create the agent executor with the system prompt
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
