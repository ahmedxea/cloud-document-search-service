"""
Command-line interface for document search.
Calls the FastAPI search endpoint and displays results.

Usage:
    python search_cli.py "your search query"
    python search_cli.py "your search query" --limit 5
"""
import sys
import requests
import click
from typing import Optional

# API configuration
API_BASE_URL = "http://localhost:8000"


def check_api_status() -> bool:
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False


def search_documents(query: str, limit: int = 10) -> Optional[dict]:
    """
    Call the search API endpoint.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        Search results dict or None if error
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/search",
            params={"q": query, "limit": limit},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            click.echo(f"Error: API returned status {response.status_code}", err=True)
            click.echo(f"Details: {response.text}", err=True)
            return None
            
    except requests.exceptions.Timeout:
        click.echo("Error: Request timed out", err=True)
        return None
    except requests.exceptions.ConnectionError:
        click.echo("Error: Could not connect to API", err=True)
        return None
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        return None


def display_results(data: dict):
    """
    Display search results in a formatted way.
    
    Args:
        data: Search results dictionary from API
    """
    query = data.get('query', '')
    total = data.get('total_results', 0)
    results = data.get('results', [])
    
    # Header
    click.echo()
    click.echo("=" * 70)
    click.echo(f"Search Results for: '{query}'")
    click.echo("=" * 70)
    click.echo(f"Found {total} result(s)\n")
    
    if not results:
        click.echo("No documents found matching your query.")
        click.echo()
        return
    
    # Display each result
    for i, result in enumerate(results, 1):
        # Result number and file name
        click.echo(f"{i}. ", nl=False)
        click.secho(result['file_name'], fg='cyan', bold=True)
        
        # Score
        score = result.get('score', 0)
        click.echo(f"   Score: ", nl=False)
        click.secho(f"{score}", fg='green')
        
        # Path
        click.echo(f"   Path:  {result['file_path']}")
        
        # Type
        click.echo(f"   Type:  {result['mime_type']}")
        
        # URL (shortened for display)
        url = result.get('url', '')
        if url:
            display_url = url if len(url) < 60 else url[:57] + "..."
            click.echo(f"   URL:   {display_url}")
        
        # Highlights (matched snippets)
        highlights = result.get('highlights', [])
        if highlights:
            click.echo(f"   Match: ", nl=False)
            # Remove HTML tags and truncate
            highlight_text = highlights[0].replace('<em>', '').replace('</em>', '')
            if len(highlight_text) > 80:
                highlight_text = highlight_text[:77] + "..."
            click.secho(f"...{highlight_text}...", fg='yellow')
        
        click.echo()
    
    # Footer
    click.echo("=" * 70)
    click.echo()


@click.command()
@click.argument('query', type=str)
@click.option(
    '--limit', '-l',
    default=10,
    type=int,
    help='Maximum number of results to return (default: 10)'
)
@click.option(
    '--url',
    default=API_BASE_URL,
    help=f'API base URL (default: {API_BASE_URL})'
)
def main(query: str, limit: int, url: str):
    """
    Search documents from the command line.
    
    QUERY: The search term or phrase to look for.
    
    Examples:
        python search_cli.py "engineering"
        python search_cli.py "API documentation" --limit 5
        python search_cli.py "laptop" -l 3
    """
    global API_BASE_URL
    API_BASE_URL = url
    
    # Validate limit
    if limit < 1 or limit > 100:
        click.echo("Error: Limit must be between 1 and 100", err=True)
        sys.exit(1)
    
    # Check if API is running
    if not check_api_status():
        click.echo("Error: Search API is not running!", err=True)
        click.echo("\nPlease start the API server first:", err=True)
        click.echo("  python -m search_service.api.app", err=True)
        click.echo("  OR", err=True)
        click.echo("  uvicorn search_service.api.app:app --reload", err=True)
        sys.exit(1)
    
    # Perform search
    results = search_documents(query, limit)
    
    if results is None:
        sys.exit(1)
    
    # Display results
    display_results(results)


if __name__ == '__main__':
    main()
