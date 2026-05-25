import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI(title="Quadra", description="Учебный проект: 4 модуля в одном приложении")

# Статика
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Подключаем роутеры
from src.api.tracker_routes import router as tracker_router
from src.api.qr_routes import router as qr_router
from src.api.budget_routes import router as budget_router
from src.api.email_routes import router as email_router, init_email

app.include_router(tracker_router)
app.include_router(qr_router)
app.include_router(budget_router)
app.include_router(email_router)

# Инициализация email (только если .env заполнен)
smtp_host = os.getenv("SMTP_HOST", "")
if smtp_host:
    from src.email_module.mailer import Mailer
    mailer = Mailer(
        host=smtp_host,
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_USERNAME", ""),
        password=os.getenv("SMTP_PASSWORD", ""),
        sender_name=os.getenv("SMTP_SENDER_NAME", "Quadra"),
        sender_email=os.getenv("SMTP_SENDER_EMAIL", ""),
    )
    init_email(mailer)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    from src.api.tracker_routes import _service as tracker_svc
    from src.api.budget_routes import _service as budget_svc
    from src.api.email_routes import _queue

    balance = tracker_svc.get_balance()
    transactions = tracker_svc.transactions[-5:][::-1]
    trips = budget_svc.list_profiles()[-3:]
    email_jobs = _queue.get_status()[-5:][::-1] if _queue else []

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "balance": balance,
            "transactions": transactions,
            "trips": trips,
            "email_jobs": email_jobs,
        },
    )
