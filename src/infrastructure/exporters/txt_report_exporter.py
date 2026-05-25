import re
from src.application.interfaces.i_report_exporter import IReportExporter
from src.application.dto.trip_dto import TripSummaryResponse

class TxtReportExporter(IReportExporter):
    def export(self, summary: TripSummaryResponse) -> str:
        safe_name = re.sub(r'[^\w\-_]', '_', summary.name.lower())
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        filename = f"report_{safe_name}.txt"
        
        lines = [
            "==========================================",
            "           ИТОГОВЫЙ ОТЧЕТ ПОЕЗДКИ          ",
            "==========================================",
            f"Поездка: {summary.name}",
            f"Даты: {summary.start_date} - {summary.end_date}",
            f"Количество участников: {summary.people_count}",
            f"Стоимость билета (на одного): {summary.ticket_price_per_person:.2f} руб.",
            f"Всего за билеты (на всех): {summary.transport_total:.2f} руб.",
            "------------------------------------------"
        ]
        
        if summary.expenses:
            lines.append("Прочие расходы по категориям:")
            for idx, exp in enumerate(summary.expenses, 1):
                lines.append(f"  {idx}. {exp.category_name}: {exp.amount:.2f} руб.")
            lines.append(f"Всего прочих расходов: {summary.expenses_total:.2f} руб.")
        else:
            lines.append("Прочих расходов не добавлено.")
            
        lines.extend([
            "------------------------------------------",
            f"ОБЩИЕ ЗАТРАТЫ НА ПОЕЗДКУ: {summary.grand_total:.2f} руб.",
            f"СРЕДНИЙ РАСХОД НА ЧЕЛОВЕКА: {summary.cost_per_person:.2f} руб.",
            "=========================================="
        ])
        
        content = "\n".join(lines)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
        return filename