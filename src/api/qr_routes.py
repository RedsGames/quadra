from fastapi import APIRouter, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
import io

from src.qr_module.qr_utils import qr_to_bytes, batch_qr_zip

router = APIRouter(prefix="/qr", tags=["qr"])
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
async def qr_page(request: Request):
    return templates.TemplateResponse(request, "qr.html")


@router.post("/generate")
async def generate_qr(
    data: str = Form(...),
    caption: str = Form(""),
    box_size: int = Form(10),
):
    png = qr_to_bytes(data, caption, box_size)
    return Response(content=png, media_type="image/png")


@router.post("/batch")
async def batch_qr(
    file: UploadFile = File(...),
    box_size: int = Form(10),
):
    content = await file.read()
    lines = content.decode("utf-8").splitlines()
    zip_bytes = batch_qr_zip(lines, box_size)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=qr_codes.zip"},
    )
