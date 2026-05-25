"""CLI entry point for the email auto-sender.

Usage examples::

    python main.py send --to alice@example.com --subject "Daily" \\
        --template daily_report.html --context '{"report_date":"2026-05-24"}'

    python main.py queue --to bob@example.com --subject "Weekly" \\
        --template weekly_report.html --context '{"week_number":21}'

    python main.py process
    python main.py status
"""

import argparse
import json
import sys

from src.config import load_config
from src.logger import setup_logger
from src.mailer import Mailer, MailerError
from src.models import EmailMessage
from src.queue_manager import QueueManager
from src.template_engine import TemplateEngine


def cmd_send(args: argparse.Namespace, config, logger) -> None:
    """Render a template and send the email immediately (bypasses queue)."""
    engine = TemplateEngine(config.templates_dir)
    mailer = Mailer(config.smtp)

    context = json.loads(args.context) if args.context else {}
    body_html = engine.render(args.template, context)

    message = EmailMessage(
        to=args.to.split(","),
        subject=args.subject,
        body_html=body_html,
    )

    try:
        mailer.send(message)
        print(f"Email sent successfully to {args.to}")
    except MailerError as exc:
        logger.error("Direct send failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_queue_add(args: argparse.Namespace, config, logger) -> None:
    """Render a template and add the result to the send queue."""
    engine = TemplateEngine(config.templates_dir)
    queue = QueueManager(config.queue_file, config.max_retries)

    context = json.loads(args.context) if args.context else {}
    body_html = engine.render(args.template, context)

    message = EmailMessage(
        to=args.to.split(","),
        subject=args.subject,
        body_html=body_html,
    )

    item_id = queue.add(message)
    print(f"Queued with id: {item_id}")


def cmd_process(args: argparse.Namespace, config, logger) -> None:
    """Attempt delivery for every pending/retrying item in the queue."""
    queue = QueueManager(config.queue_file, config.max_retries)
    mailer = Mailer(config.smtp)
    pending = queue.get_pending()

    if not pending:
        print("Queue is empty — nothing to process.")
        return

    print(f"Processing {len(pending)} item(s)...")
    sent = failed = 0

    for item in pending:
        try:
            mailer.send(item.message)
            queue.mark_sent(item.item_id)
            print(f"  [OK]   {item.item_id[:8]}  {item.message.subject!r}")
            sent += 1
        except MailerError as exc:
            queue.mark_failed(item.item_id, str(exc))
            print(f"  [FAIL] {item.item_id[:8]}  {exc}", file=sys.stderr)
            failed += 1

    print(f"\nResult — sent: {sent}, failed: {failed}")


def cmd_status(args: argparse.Namespace, config, logger) -> None:
    """Print queue statistics to stdout."""
    queue = QueueManager(config.queue_file, config.max_retries)
    stats = queue.stats()
    width = max(len(k) for k in stats)
    print("Queue statistics:")
    for key, value in stats.items():
        print(f"  {key:<{width}} : {value}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="email-sender",
        description="Automated email report sender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--config", default=None, metavar="PATH", help="Path to config.ini")

    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # --- send ---
    p_send = sub.add_parser("send", help="Send an email immediately")
    p_send.add_argument("--to", required=True, help="Recipient(s), comma-separated")
    p_send.add_argument("--subject", required=True, help="Email subject")
    p_send.add_argument(
        "--template", required=True, help="Template filename, e.g. daily_report.html"
    )
    p_send.add_argument("--context", default=None, help="JSON object of template variables")

    # --- queue ---
    p_queue = sub.add_parser("queue", help="Add email to the send queue")
    p_queue.add_argument("--to", required=True)
    p_queue.add_argument("--subject", required=True)
    p_queue.add_argument("--template", required=True)
    p_queue.add_argument("--context", default=None)

    # --- process ---
    sub.add_parser("process", help="Send all pending items in the queue")

    # --- status ---
    sub.add_parser("status", help="Show queue statistics")

    return parser


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate command handler."""
    parser = _build_parser()
    args = parser.parse_args()

    config = load_config(args.config)
    logger = setup_logger(config.log_file)

    handlers = {
        "send": cmd_send,
        "queue": cmd_queue_add,
        "process": cmd_process,
        "status": cmd_status,
    }

    handlers[args.command](args, config, logger)


if __name__ == "__main__":
    main()
