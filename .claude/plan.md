# Phase 1 Implementation Plan — FastAPI Skeleton

## Objective
Set up a working FastAPI application with proper project structure, configuration management, and a health check endpoint. When complete, the server should boot cleanly and respond to requests.

## Steps

### 1. Create backend folder structure
Create the complete folder hierarchy as specified in the plan:
```
backend/
  app/
    main.py
    api/
      routes_upload.py
      routes_projects.py
    preprocessing/
      pdf_parser.py
      docx_parser.py
      vision_extractor.py
      normalizer.py
    agents/
      graph.py
      state.py
      nodes/
        extract.py
        classify.py
        risk.py
        complexity.py
        questions.py
    db/
      models.py
      session.py
    core/
      config.py
      claude_client.py
  requirements.txt
  Dockerfile
  .env.example
```

Add `__init__.py` files to make Python packages:
- `app/__init__.py`
- `app/api/__init__.py`
- `app/preprocessing/__init__.py`
- `app/agents/__init__.py`
- `app/agents/nodes/__init__.py`
- `app/db/__init__.py`
- `app/core/__init__.py`

### 2. Create requirements.txt
Initial dependencies for Phase 1:
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.1
pydantic-settings==2.5.2
python-dotenv==1.0.1
```

Note: Additional dependencies will be added in later phases:
- Phase 2: PyMuPDF, pdfplumber, python-docx, anthropic
- Phase 3: langgraph, langchain-anthropic
- Phase 4: sqlalchemy, psycopg2-binary, alembic

### 3. Create configuration system (app/core/config.py)
Use pydantic-settings to load environment variables:
- ANTHROPIC_API_KEY (str)
- DATABASE_URL (str, with default for SQLite)
- FILE_STORAGE_PATH (str, with default to "./uploads")
- HOST (str, default "0.0.0.0")
- PORT (int, default 8000)
- DEBUG (bool, default False)

Create a singleton Settings instance that can be imported throughout the app.

### 4. Create .env.example
Template file showing required environment variables with placeholder values:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxx
DATABASE_URL=sqlite:///./clientscope.db
FILE_STORAGE_PATH=./uploads
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### 5. Create main FastAPI app (app/main.py)
- Import FastAPI and create app instance
- Add metadata (title="ClientScope AI", version="0.1.0")
- Include CORS middleware (allow all origins for development)
- Create health check endpoint: `GET /health`
  - Returns: `{"status": "healthy", "service": "clientscope-ai"}`
- Add startup event handler that logs configuration (without secrets)
- Import and include API routers (will be empty for now)

### 6. Create placeholder API route files
Create empty router files with basic structure:
- `app/api/routes_upload.py` — APIRouter with prefix="/upload"
- `app/api/routes_projects.py` — APIRouter with prefix="/projects"

Each should have:
- Router instance created
- One placeholder endpoint that returns "Not implemented yet"
- Docstring explaining what this router will handle

### 7. Create placeholder files for other modules
For all other .py files in the structure, create them with:
- Module docstring explaining purpose
- TODO comment referencing which phase implements it
- Pass statement or minimal placeholder code

This prevents import errors and documents the architecture.

### 8. Create run script
Create `backend/run.py` for easy development server startup:
```python
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
```

### 9. Verification steps
After implementation:
1. Copy .env.example to .env and add a dummy API key
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python run.py` or `uvicorn app.main:app --reload`
4. Test health endpoint: `curl http://localhost:8000/health`
5. Verify the response is JSON with status "healthy"
6. Check that server logs show startup without errors
7. Verify hot reload works by changing health endpoint message

## Success Criteria
- [ ] All folders and files created with proper structure
- [ ] Server starts without import errors
- [ ] Health check endpoint returns correct JSON response
- [ ] Configuration loads from .env file
- [ ] No warnings or errors in server logs
- [ ] Project structure matches the plan document exactly

## Out of Scope for Phase 1
- Any actual file parsing logic
- Agent pipeline implementation
- Database connections (models created, but not initialized)
- Claude API integration
- File upload handling
- Docker configuration (file created but not populated)

## Estimated Time
~20 minutes of development + 5 minutes verification
