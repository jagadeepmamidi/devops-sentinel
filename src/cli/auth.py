"""
DevOps Sentinel CLI - Authentication Module
============================================

Handles user authentication via browser redirect (OAuth-style).
Similar to how GitHub CLI, Stripe CLI, and Vercel CLI work.

Usage:
    sentinel login          - Opens browser for login
    sentinel login --token  - Use API token (for CI/CD)
    sentinel logout         - Clear saved credentials
    sentinel whoami         - Show current user
"""

import os
import sys
import json
import time
import webbrowser
import secrets
import hashlib
from pathlib import Path
from typing import Optional, Dict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

import click

# Config directory - ~/.sentinel
CONFIG_DIR = Path.home() / '.sentinel'
CONFIG_FILE = CONFIG_DIR / 'config.json'
CREDENTIALS_FILE = CONFIG_DIR / 'credentials.json'


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set restrictive permissions on Unix
    if sys.platform != 'win32':
        CONFIG_DIR.chmod(0o700)


def save_credentials(access_token: str, refresh_token: str, user: Dict):
    """Save user credentials securely."""
    ensure_config_dir()
    
    credentials = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user,
        'saved_at': time.time()
    }
    
    CREDENTIALS_FILE.write_text(json.dumps(credentials, indent=2))
    
    # Set restrictive permissions on Unix
    if sys.platform != 'win32':
        CREDENTIALS_FILE.chmod(0o600)


def load_credentials() -> Optional[Dict]:
    """Load saved credentials if they exist."""
    if not CREDENTIALS_FILE.exists():
        return None
    
    try:
        return json.loads(CREDENTIALS_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return None


def clear_credentials():
    """Remove saved credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def get_current_user() -> Optional[Dict]:
    """Get the current logged-in user."""
    creds = load_credentials()
    if creds:
        return creds.get('user')
    return None


def get_access_token() -> Optional[str]:
    """Get the current access token."""
    creds = load_credentials()
    if creds:
        return creds.get('access_token')
    return None


def is_logged_in() -> bool:
    """Check if user is logged in."""
    return load_credentials() is not None


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    token_data = None
    
    def log_message(self, format, *args):
        """Suppress HTTP logs."""
        pass
    
    def do_GET(self):
        """Handle the callback from Supabase auth."""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        # Check for access token in URL fragment (won't work with server-side)
        # Supabase returns tokens in the hash, so we need a simple HTML page
        # that extracts them and sends to our callback
        
        if parsed.path == '/callback':
            # Check if this is the token submission
            access_token = query_params.get('access_token', [None])[0]
            refresh_token = query_params.get('refresh_token', [None])[0]
            
            if access_token:
                # Store the tokens
                AuthCallbackHandler.token_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token or ''
                }
                
                # Send success page
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
<!DOCTYPE html>
<html>
<head>
    <title>DevOps Sentinel - Login Successful</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #0a0a0a;
            color: #fff;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        .icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        h1 {
            margin: 0 0 10px;
            font-size: 24px;
        }
        p {
            color: #888;
            margin: 0;
        }
        .hint {
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">✓</div>
        <h1>Login Successful!</h1>
        <p>You can close this window and return to the terminal.</p>
        <p class="hint">DevOps Sentinel is now authenticated.</p>
    </div>
</body>
</html>
"""
                self.wfile.write(success_html.encode())
            else:
                # Landing page that extracts tokens from hash
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                extract_html = """
<!DOCTYPE html>
<html>
<head>
    <title>DevOps Sentinel - Authenticating...</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #0a0a0a;
            color: #fff;
        }
        .container { text-align: center; }
        .spinner {
            border: 3px solid #333;
            border-top: 3px solid #fff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner"></div>
        <p>Completing authentication...</p>
    </div>
    <script>
        // Extract tokens from URL hash
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');
        
        if (accessToken) {
            // Redirect to callback with tokens as query params
            window.location.href = '/callback?access_token=' + accessToken + 
                '&refresh_token=' + (refreshToken || '');
        } else {
            document.body.innerHTML = '<div class="container"><p>Authentication failed. Please try again.</p></div>';
        }
    </script>
</body>
</html>
"""
                self.wfile.write(extract_html.encode())
        else:
            self.send_response(404)
            self.end_headers()


def start_callback_server(port: int = 54321) -> HTTPServer:
    """Start local HTTP server for OAuth callback."""
    server = HTTPServer(('localhost', port), AuthCallbackHandler)
    return server


def browser_login(supabase_url: str, redirect_port: int = 54321) -> Optional[Dict]:
    """
    Perform browser-based login.
    
    Opens browser to Supabase auth page, waits for callback with tokens.
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Callback URL
    redirect_uri = f'http://localhost:{redirect_port}/callback'
    
    # Build Supabase auth URL
    # For magic link or OAuth providers
    auth_url = f"{supabase_url}/auth/v1/authorize"
    
    # Actually, Supabase's hosted auth UI is at a different path
    # Let's use the project's hosted auth page
    project_ref = supabase_url.replace('https://', '').split('.')[0]
    
    # Construct the auth URL for the hosted auth UI
    auth_url = f"https://{project_ref}.supabase.co/auth/v1/authorize?provider=email&redirect_to={redirect_uri}"
    
    # Start local server
    server = start_callback_server(redirect_port)
    
    # Reset token data
    AuthCallbackHandler.token_data = None
    
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Opening browser for authentication...")
    click.echo(f"  If browser doesn't open, visit: {auth_url[:60]}...")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback (with timeout)
    click.echo("  Waiting for authentication...")
    
    server.timeout = 120  # 2 minute timeout
    start_time = time.time()
    
    while AuthCallbackHandler.token_data is None:
        server.handle_request()
        if time.time() - start_time > 120:
            click.echo(click.style("\n  Authentication timed out.", fg='red'))
            return None
    
    server.server_close()
    
    return AuthCallbackHandler.token_data


def token_login(token: str, supabase_url: str) -> Optional[Dict]:
    """
    Login using an API token.
    
    For CI/CD environments where browser isn't available.
    """
    try:
        import httpx
        
        # Verify token with Supabase
        response = httpx.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                'Authorization': f'Bearer {token}',
                'apikey': os.getenv('SUPABASE_ANON_KEY', '')
            },
            timeout=10
        )
        
        if response.status_code == 200:
            user = response.json()
            return {
                'access_token': token,
                'refresh_token': '',
                'user': user
            }
        else:
            return None
    except Exception as e:
        click.echo(f"  Error: {str(e)}")
        return None


def require_auth(func):
    """Decorator to require authentication for a command."""
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            click.echo(click.style('Error: Not logged in. Run `sentinel login` first.', fg='red'))
            sys.exit(1)
        return func(*args, **kwargs)
    return wrapper


# CLI Commands

@click.command()
@click.option('--token', '-t', help='API token for non-interactive login (CI/CD)')
@click.option('--supabase-url', envvar='SUPABASE_URL', help='Supabase project URL')
def login(token: Optional[str], supabase_url: Optional[str]):
    """
    Authenticate with DevOps Sentinel.
    
    Opens browser for secure login. Use --token for CI/CD environments.
    
    Examples:
    
        sentinel login
        
        sentinel login --token YOUR_API_TOKEN
    """
    # Check for existing login
    if is_logged_in():
        user = get_current_user()
        email = user.get('email', 'Unknown') if user else 'Unknown'
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Already logged in as {email}")
        
        if not click.confirm("  Do you want to re-authenticate?"):
            return
        
        clear_credentials()
    
    # Check for Supabase URL
    if not supabase_url:
        supabase_url = os.getenv('SUPABASE_URL')
    
    if not supabase_url:
        click.echo(click.style("\nError: SUPABASE_URL not configured.", fg='red'))
        click.echo("  Run `sentinel init` first or set SUPABASE_URL environment variable.")
        return
    
    # Perform login
    if token:
        # Token-based login for CI/CD
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Authenticating with API token...")
        result = token_login(token, supabase_url)
    else:
        # Browser-based login
        result = browser_login(supabase_url)
    
    if result:
        # Get user info
        user = result.get('user', {})
        access_token = result.get('access_token', '')
        refresh_token = result.get('refresh_token', '')
        
        # Save credentials
        save_credentials(access_token, refresh_token, user)
        
        email = user.get('email', 'Unknown')
        click.echo(f"\n{click.style('✓', fg='green')} Successfully logged in as {email}")
        click.echo(f"  Credentials saved to {CONFIG_DIR}")
        click.echo(f"\n  Next steps:")
        click.echo(f"    sentinel status    - Check configuration")
        click.echo(f"    sentinel monitor   - Start monitoring")
    else:
        click.echo(click.style("\n✗ Authentication failed.", fg='red'))


@click.command()
def logout():
    """Log out and clear saved credentials."""
    if not is_logged_in():
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Not currently logged in.")
        return
    
    user = get_current_user()
    email = user.get('email', 'Unknown') if user else 'Unknown'
    
    clear_credentials()
    click.echo(f"\n{click.style('✓', fg='green')} Logged out from {email}")
    click.echo(f"  Credentials removed from {CONFIG_DIR}")


@click.command()
def whoami():
    """Show current logged-in user."""
    if not is_logged_in():
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Not logged in.")
        click.echo("  Run `sentinel login` to authenticate.")
        return
    
    user = get_current_user()
    creds = load_credentials()
    
    click.echo(f"\n{click.style('Current User', bold=True)}")
    click.echo("─" * 40)
    click.echo(f"  Email: {user.get('email', 'Unknown')}")
    click.echo(f"  ID: {user.get('id', 'Unknown')[:8]}...")
    
    if creds and creds.get('saved_at'):
        import datetime
        saved = datetime.datetime.fromtimestamp(creds['saved_at'])
        click.echo(f"  Authenticated: {saved.strftime('%Y-%m-%d %H:%M')}")
    
    click.echo(f"\n  Config: {CONFIG_DIR}")
    click.echo()
