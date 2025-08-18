from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import (
    ParseRequest,
    AnalyzeRequest,
    RewriteRequest,
    RewriteResponse,
    AnalyzeResponse,
)
from .services.parse import parse_text
from .services.analyze import analyze
from .services.rewrite import rewrite
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from .services.parse import parse_text, parse_file
from .services.export import resume_to_docx
from io import BytesIO

app = FastAPI(title="Resume Tailor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/parse")
def parse(req: ParseRequest):
    try:
        parsed = parse_text(req.type, req.content, req.filename)
        return {"parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_endpoint(req: AnalyzeRequest):
    result = analyze(req.resume.dict(), req.jd.dict())
    return result


@app.post("/api/rewrite", response_model=RewriteResponse)
def rewrite_endpoint(req: RewriteRequest):
    result = rewrite(req.section, req.text, req.constraints or {})
    return result


@app.post("/api/parse-upload")
async def parse_upload(
    type: str = Form(...), file: UploadFile = File(...)  # 'resume' | 'jd'
):
    try:
        parsed = parse_file(type, file.filename, file.file)
        return {"parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/export/docx")
def export_docx(resume: dict):
    try:
        data = resume_to_docx(resume)
        return StreamingResponse(
            BytesIO(data),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="resume-tailored.docx"'}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
