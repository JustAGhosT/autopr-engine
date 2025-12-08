"""GitHub App Setup Page.

Displays setup completion status after installation.
"""

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

setup_router = APIRouter(prefix="", tags=["github-app"])

# Templates directory
templates = Jinja2Templates(directory="autopr/integrations/github_app/templates")


@setup_router.get("/setup")
async def setup_page(
    installation_id: str | None = Query(None),
    account: str | None = Query(None),
) -> HTMLResponse:
    """Display setup completion page.

    Args:
        installation_id: GitHub App installation ID
        account: Account name where app was installed

    Returns:
        HTML response with setup status
    """
    # Simple HTML response (can be enhanced with templates)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Setup Complete - AutoPR</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .success {{
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .loading {{
                text-align: center;
                padding: 40px;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Setup Complete! 🎉</h1>
            {"<div class='success'>✅ GitHub App installed successfully for <strong>" + account + "</strong></div>" if account else ""}
            <div>
                <h2>Next Steps</h2>
                <ol>
                    <li>Configure Azure credentials (if not done automatically)</li>
                    <li>Deploy infrastructure using the Azure Infrastructure workflow</li>
                    <li>Deploy the application using the Deploy to Azure workflow</li>
                </ol>
            </div>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)

