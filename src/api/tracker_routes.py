import json
from datetime import date

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.tracker.services import FinanceService
from src.tracker.storage import JsonStorage

router = APIRouter(prefix="/tracker", tags=["tracker"])
templates = Jinja2Templates(directory="templates")

_storage = JsonStorage()
_service = FinanceService(_storage, "data/transactions.json")


def _svc() -> FinanceService:
    return _service


@router.get("", response_class=HTMLResponse)
async def tracker_page(request: Request, date_filter: str = "", category: str = ""):
    svc = _svc()
    transactions = svc.filter_transactions(
        date=date_filter or None,
        category=category or None,
    )
    balance = svc.get_balance()
    chart_data = svc.get_chart_data()
    return templates.TemplateResponse(
        request,
        "tracker.html",
        {
            "transactions": transactions,
            "balance": balance,
            "chart_labels": json.dumps(list(chart_data.keys())),
            "chart_values": json.dumps(list(chart_data.values())),
            "date_filter": date_filter,
            "category": category,
        },
    )


@router.post("/add")
async def add_transaction(
    t_type: str = Form(..., alias="type"),
    category: str = Form(...),
    amount: float = Form(...),
    trans_date: str = Form(..., alias="date"),
    description: str = Form(""),
):
    if amount <= 0:
        return PlainTextResponse("Сумма должна быть > 0", status_code=422)
    _svc().add_transaction(t_type, category, amount, trans_date, description)
    return RedirectResponse("/tracker", status_code=303)


@router.post("/delete/{t_id}")
async def delete_transaction(t_id: int):
    _svc().delete_transaction(t_id)
    return RedirectResponse("/tracker", status_code=303)


@router.get("/export", response_class=PlainTextResponse)
async def export_transactions():
    text = _svc().export_text()
    return PlainTextResponse(
        text,
        headers={"Content-Disposition": "attachment; filename=report.txt"},
    )
