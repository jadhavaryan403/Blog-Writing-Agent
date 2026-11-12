# ✨ AI Blog Generation Platform

An AI-powered full-stack blog generation platform that uses a multi-agent workflow to plan, research, and write high-quality blogs by adding relevant images. The application combines LLMs, human-in-the-loop approval, and AI-assisted editing to generate accurate and customizable content.

---

## Features

### Multi-Agent Blog Generation
- Generates complete blogs using a LangGraph multi-agent workflow.
- Dedicated agents for planning, research, writing, and quality review.
- Adds images relevant to the blog section
- Produces structured, high-quality long-form content.


### Human-in-the-Loop Approval
- AI first generates a blog outline.
- Users can review and edit the outline before generation.
- Workflow resumes only after user approval.


### AI Section Editing
- Edit any section of a generated blog using natural language instructions.
- Individual sections are regenerated without affecting the rest of the blog.


### User Preferences
Customize blog generation with:
- Writing tone
- Writing style
- Technical depth
- Target language
- Target word count

Preferences can be saved as defaults or overridden per blog.


### AI Guardrails
- Topic validation before generation.
- Prompt injection detection for blog section editing.
- Structured LLM outputs using Pydantic models.


### Authentication
- JWT-based authentication.
- Secure password hashing.
- User-specific blogs and preferences.


### Workflow Persistence
- Workflow state stored in PostgreSQL.
- Resume interrupted workflows.
- Persistent blog versions and generation history.


### User personal metrics
The user can view:
- The number of blogs created
- The total tokens taken by each blog
- The total tokens consumed by all blogs combined
- The cost required to create the blogs in dashboard


### Observability
- Used LangSmith to bring observability to the AI agent.

---

# Workflow

<img width="1536" height="1024" alt="Blog Generation Workflow Diagram" src="https://github.com/user-attachments/assets/64b45933-9145-4751-a4b7-caf3000aab4a" />

---

# Tech Stack

## Backend

- Python
- FastAPI
- LangGraph
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic
- JWT Authentication
- AsyncIO
- LangSmith


## AI & LLM

- Groq API
- Structured Outputs
- LLM Guardrails
- Tavily API (for research)
- SerpAPI (for images)


## Frontend

- React
- 

## Deployment

- Render
- PostgreSQL (Neon Database)

---

# Key Features

- Multi-agent AI workflow
- Human approval before generation
- AI-powered section editing
- Version history
- User preference management
- Prompt injection protection
- Topic validation
- JWT Authentication
- PostgreSQL persistence
- Fully asynchronous backend
- REST API architecture
- Observability using Langsmith

---

# Webpage design

<img width="1919" height="1027" alt="Dashboard Page" src="https://github.com/user-attachments/assets/bf132024-259a-4997-8f78-18cc21c57bf9" />



<img width="1920" height="1032" alt="Blog View Page" src="https://github.com/user-attachments/assets/b28d4628-0831-43e4-8d0c-a57476079eed" />

---

# Future Improvements

- Caching blogs
- Export blogs as PDF and Markdown
- Support multiple LLM providers
- Blog sharing and collaboration
- SEO optimization
- RAG-based research agent
- Streaming generation

---

# Deployed link

Live_Demo(https://blog-writing-agent-1-y6mx.onrender.com/)
This will take 30-40 sec to start the backend deployed on render.

---
