import click
from . import database_handler, event_processor

@click.group()
def cli():
    """Flight Report Assistant CLI"""
    pass

@cli.command()
def init():
    """Initializes the SQLite database."""
    db = database_handler.get_database_handler()
    db.init_db()

@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
def ingest(files):
    """Ingests and processes flight reports from JSON files."""
    if not files:
        click.echo("Error: Please provide at least one file path.", err=True)
        return
    event_processor.process_and_store_files(files)

@cli.command()
@click.argument('query_type')
def stats(query_type):
    """Shows statistics. Currently supports: category"""
    db = database_handler.get_database_handler()
    if query_type == "category":
        results = db.get_stats_by_category()
        if not results:
            click.echo("No data found. Ingest some files first.")
            return
            
        click.echo("--- Events per Category ---")
        for category, count in results:
            click.echo(f"{category:<20} | {count}")
    else:
        click.echo(f"Unknown stat type: {query_type}", err=True)

@cli.command()
@click.option('--severity', required=True, type=click.Choice(['low', 'medium', 'high', 'critical'], case_sensitive=False))
def list(severity):
    """Lists reports by severity."""
    db = database_handler.get_database_handler()
    results = db.list_reports_by_severity(severity)
    if not results:
        click.echo(f"No reports found with severity '{severity}'.")
        return

    click.echo(f"\n--- Reports with Severity: {severity.upper()} ---")
    for report in results:
        click.echo(f"ID: {report['id']}")
        click.echo(f"  Timestamp: {report['timestamp']}")
        click.echo(f"  Category:  {report['category']}")
        click.echo(f"  Summary:   {report['summary']}")
        click.echo("-" * 20)

@cli.command()
@click.option('--id', 'report_id', required=True, type=str, help="The ID of the report to show.")
def show(report_id):
    """Shows the full details of a specific report."""
    db = database_handler.get_database_handler()
    report = db.get_report_by_id(report_id)
    if not report:
        click.echo(f"Error: Report with ID '{report_id}' not found.", err=True)
        return

    click.echo("\n--- Full Report Details ---")
    for key, value in report.items():
        click.echo(f"{key.capitalize():<15}: {value}")
    click.echo("-" * 27)