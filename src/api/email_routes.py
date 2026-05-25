import os
from datetime import datetime

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.email_module.mailer import Mailer
from src.email_module.queue_manager import EmailQueueManager

router = APIRouter(prefix="/email", tags=["email"])
templates = Jinja2Templates(directory="templates")

# Mailer инициализируется из env при старте приложения
_mailer: Mailer | None = None
_queue: EmailQueueManager | None = None


def init_email(mailer: Mailer):
    global _mailer, _queue
    _mailer = mailer
    _queue = EmailQueueManager(mailer)


def _get_queue() -> EmailQueueManager | None:
    return _queue


@router.get("", response_class=HTMLResponse)
async def email_page(request: Request):
    queue = _get_queue()
    jobs = queue.get_status() if queue else []
    configured = _mailer is not None
    return templates.TemplateResponse(
        request,
        "email.html",
        {"jobs": jobs, "configured": configured},
    )


@router.post("/send")
async def send_email(
    request: Request,
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
):
    queue = _get_queue()
    if not queue:
        return JSONResponse({"error": "Email не настроен. Заполните .env"}, status_code=503)
    result = queue.send_now(to, subject, body)
    jobs = queue.get_status()
    return templates.TemplateResponse(
        request,
        "email.html",
        {"jobs": jobs, "configured": True, "last_result": result},
    )


@router.post("/schedule")
async def schedule_email(
    to: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    run_at: str = Form(...),
):
    queue = _get_queue()
    if not queue:
        return JSONResponse({"error": "Email не настроен"}, status_code=503)
    run_date = datetime.fromisoformat(run_at)
    result = queue.schedule(to, subject, body, run_date)
    return JSONResponse(result)


@router.get("/status", response_class=JSONResponse)
async def email_status():
    queue = _get_queue()
    return queue.get_status() if queue else []
