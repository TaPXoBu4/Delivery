import click
from flask import Flask, current_app
from flask.cli import with_appcontext

from domain.use_cases import UseCases


def register_cli(app: Flask) -> None:
    app.cli.add_command(orders_cli)


@click.group("orders")
def orders_cli() -> None:
    pass


@orders_cli.command("cleanup")
@click.option(
    "--months",
    type=int,
    default=None,
    help="Delete orders older than this many months.",
)
@with_appcontext
def cleanup_orders(months: int | None) -> None:
    retention_months = (
        current_app.config["ORDER_RETENTION_MONTHS"]
        if months is None
        else months
    )
    if retention_months < 1:
        raise click.BadParameter("months must be a positive integer")

    use_cases: UseCases = current_app.extensions["use_cases"]
    deleted_count = use_cases.delete_orders_older_than_months(retention_months)
    click.echo(
        f"Deleted {deleted_count} orders older than {retention_months} months."
    )
