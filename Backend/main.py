from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import engine, reflect_db
from schemas import AnalyzeRequest, ExamplesRequest, ExamplesSummaryRequest
from queries import get_options, analyze, get_examples, get_examples_summary

app = FastAPI(title="Corpus Syntax API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    reflect_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/options")
def options():
    with engine.connect() as conn:
        return get_options(conn)


@app.post("/api/analyze")
def analyze_endpoint(params: AnalyzeRequest):
    try:
        with engine.connect() as conn:
            return analyze(conn, params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/examples")
def examples_endpoint(params: ExamplesRequest):
    try:
        with engine.connect() as conn:
            return get_examples(conn, params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/examples/summary")
def examples_summary_endpoint(params: ExamplesSummaryRequest):
    try:
        with engine.connect() as conn:
            return get_examples_summary(conn, params)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
