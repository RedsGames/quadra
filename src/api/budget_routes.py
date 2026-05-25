import json

import httpx
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.budget.service import BudgetService

router = APIRouter(prefix="/budget", tags=["budget"])
templates = Jinja2Templates(directory="templates")

_service = BudgetService("data/budgets.json")


@router.get("", response_class=HTMLResponse)
async def budget_page(request: Request):
    profiles = _service.list_profiles()
    return templates.TemplateResponse(request, "budget.html", {"profiles": profiles})


@router.post("/calculate")
async def calculate_budget(
    request: Request,
    name: str = Form(...),
    destination: str = Form(...),
    currency: str = Form(...),
    target_currency: str = Form("RUB"),
    notes: str = Form(""),
    items_json: str = Form("[]"),
):
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError:
        items = []

    profile = _service.create_profile(name, destination, currency, items, target_currency, notes)

    # Конвертация валют через frankfurter.app
    rate = 1.0
    if currency != target_currency:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"https://api.frankfurter.app/latest?from={currency}&to={target_currency}"
                )
                data = resp.json()
                rate = data["rates"].get(target_currency, 1.0)
        except Exception:
            pass  # оставляем rate=1 если API недоступен

    _service.update_converted(profile.id, rate)
    profile = _service.get_profile(profile.id)

    return templates.TemplateResponse(
        request,
        "budget.html",
        {
            "profiles": _service.list_profiles(),
            "result": profile,
            "rate": rate,
        },
    )


@router.get("/convert", response_class=JSONResponse)
async def convert_currency(from_currency: str, to_currency: str, amount: float = 1.0):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"
            )
            data = resp.json()
            rate = data["rates"].get(to_currency, 1.0)
    except Exception:
        return JSONResponse({"error": "Сервис конвертации недоступен"}, status_code=503)
    return {"from": from_currency, "to": to_currency, "rate": rate, "result": round(amount * rate, 2)}


@router.get("/{trip_id}", response_class=HTMLResponse)
async def get_profile(request: Request, trip_id: str):
    profile = _service.get_profile(trip_id)
    if not profile:
        return HTMLResponse("Поездка не найдена", status_code=404)
    return templates.TemplateResponse(
        request,
        "budget.html",
        {"profiles": _service.list_profiles(), "result": profile},
    )


@router.post("/delete/{trip_id}")
async def delete_profile(trip_id: str):
    _service.delete_profile(trip_id)
    return RedirectResponse("/budget", status_code=303)
