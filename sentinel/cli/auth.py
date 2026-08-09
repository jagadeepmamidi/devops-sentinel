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
import secrets
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode

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
        user = creds.get('user')
        if isinstance(user, dict) and user.get('id'):
            return user
    return None


def get_access_token() -> Optional[str]:
    """Get the current access token."""
    creds = load_credentials()
    if creds:
        return creds.get('access_token')
    return None


def is_logged_in() -> bool:
    """Check if user is logged in."""
    return bool(get_access_token() and get_current_user())


def resolve_supabase_key() -> Optional[str]:
    """Resolve Supabase key from supported environment aliases."""
    key = (os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY') or '').strip()
    return key or None


def fetch_user_profile(access_token: str, supabase_url: str) -> Optional[Dict]:
    """Fetch authenticated user profile from Supabase."""
    if not access_token or not supabase_url:
        return None

    try:
        import httpx

        headers = {'Authorization': f'Bearer {access_token}'}
        supabase_key = resolve_supabase_key()
        if supabase_key:
            headers['apikey'] = supabase_key

        response = httpx.get(
            f"{supabase_url.rstrip('/')}/auth/v1/user",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            user = response.json()
            if isinstance(user, dict) and user.get('id'):
                return user
        return None
    except Exception:
        return None


def extract_token_from_input(raw_input: str, expected_state: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Extract access token from raw token or callback URL input."""
    raw = (raw_input or '').strip()
    if not raw:
        return None, 'empty'

    def _parse_state_token(params: Dict[str, list]) -> Tuple[Optional[str], Optional[str]]:
        token = params.get('access_token', [None])[0]
        state = params.get('state', [None])[0]
        if expected_state and state and state != expected_state:
            return None, 'state_mismatch'
        return token, None

    if raw.startswith(('http://', 'https://')):
        parsed = urlparse(raw)
        fragment_params = parse_qs(parsed.fragment)
        query_params = parse_qs(parsed.query)

        token, err = _parse_state_token(fragment_params)
        if token or err:
            return token, err

        token, err = _parse_state_token(query_params)
        if token or err:
            return token, err

        return None, 'missing_access_token'

    if 'access_token=' in raw:
        value = raw.split('#', 1)[1] if '#' in raw else raw
        token, err = _parse_state_token(parse_qs(value))
        if token or err:
            return token, err
        return None, 'missing_access_token'

    return raw, None


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""
    
    token_data = None
    expected_state = None
    
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
            state = query_params.get('state', [None])[0]
             
            if access_token:
                expected_state = AuthCallbackHandler.expected_state
                if expected_state and state != expected_state:
                    AuthCallbackHandler.token_data = {'error': 'state_mismatch'}
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b'<html><body><h1>Authentication failed</h1><p>Invalid auth state.</p></body></html>')
                    return

                # Store the tokens
                AuthCallbackHandler.token_data = {
                    'access_token': access_token,
                    'refresh_token': refresh_token or '',
                    'state': state,
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
        <div class="icon">OK</div>
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
        
        const state = params.get('state') || '';
        if (accessToken) {
            // Redirect to callback with tokens as query params
            window.location.href = '/callback?access_token=' + encodeURIComponent(accessToken) +
                '&refresh_token=' + encodeURIComponent(refreshToken || '') +
                '&state=' + encodeURIComponent(state);
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


def build_browser_auth_url(
    supabase_url: str,
    redirect_uri: str,
    web_url: Optional[str] = None,
    state: Optional[str] = None,
    source: str = "cli",
) -> str:
    """Build browser auth URL for website-first CLI auth flow."""
    selected_web_url = (web_url or os.getenv("SENTINEL_WEB_URL", "")).strip()

    if selected_web_url:
        base = selected_web_url.rstrip("/")
        payload = {
            "supabase_url": supabase_url,
            "redirect_uri": redirect_uri,
            "source": source,
        }
        if state:
            payload["state"] = state
        query = urlencode(payload)
        return f"{base}/cli-auth?{query}"

    # Fallback direct Supabase hosted auth
    params = {
        "provider": "email",
        "redirect_to": redirect_uri,
    }
    if state:
        params["state"] = state
    return f"{supabase_url.rstrip('/')}/auth/v1/authorize?{urlencode(params)}"


def browser_login(
    supabase_url: str,
    redirect_port: int = 54321,
    web_url: Optional[str] = None
) -> Optional[Dict]:
    """
    Perform browser-based login.
    
    Opens browser to Supabase auth page, waits for callback with tokens.
    """
    # Callback URL
    redirect_uri = f'http://localhost:{redirect_port}/callback'
    auth_state = secrets.token_urlsafe(24)
    auth_url = build_browser_auth_url(
        supabase_url,
        redirect_uri,
        web_url=web_url,
        state=auth_state,
        source="cli",
    )
    
    # Start local server
    try:
        server = start_callback_server(redirect_port)
    except OSError as e:
        click.echo(click.style(f"\n  Failed to start local callback server on port {redirect_port}: {e}", fg='red'))
        return None
    
    # Reset token data
    AuthCallbackHandler.token_data = None
    AuthCallbackHandler.expected_state = auth_state
    
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Opening browser for login/signup...")
    click.echo("  Complete auth in your browser, then return to this terminal.")
    click.echo(f"  If browser doesn't open, visit: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for callback (with timeout)
    click.echo("  Waiting for authentication...")
    
    server.timeout = 120  # 2 minute timeout
    start_time = time.time()
    
    try:
        while AuthCallbackHandler.token_data is None:
            server.handle_request()
            if time.time() - start_time > 120:
                click.echo(click.style("\n  Authentication timed out.", fg='red'))
                return None
    finally:
        server.server_close()
        AuthCallbackHandler.expected_state = None

    token_data = AuthCallbackHandler.token_data or {}
    if token_data.get('error') == 'state_mismatch':
        click.echo(click.style("\n  Authentication failed: invalid auth state.", fg='red'))
        return None

    return token_data


def token_login(token: str, supabase_url: str) -> Optional[Dict]:
    """
    Login using an API token.
    
    For CI/CD environments where browser isn't available.
    """
    try:
        user = fetch_user_profile(token, supabase_url)
        if user:
            return {
                'access_token': token,
                'refresh_token': '',
                'user': user
            }
        return None
    except Exception as e:
        click.echo(f"  Error: {str(e)}")
        return None


def device_login(supabase_url: str, web_url: Optional[str]) -> Optional[Dict]:
    """
    Headless-friendly login flow.

    User opens the auth URL on any browser-enabled device, then pastes
    an access token back into the terminal.
    """
    auth_state = secrets.token_urlsafe(24)
    auth_url = build_browser_auth_url(
        supabase_url=supabase_url,
        redirect_uri="http://localhost/device",
        web_url=web_url,
        state=auth_state,
        source="device",
    )

    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Device login mode")
    click.echo("  1. Open this URL on any browser-enabled device:")
    click.echo(f"     {auth_url}")
    click.echo("  2. Complete signup/signin.")
    click.echo("  3. After redirect, copy the full callback URL from browser address bar.")
    click.echo("  4. Paste callback URL (or just access token) below.")

    raw_input = click.prompt("  Callback URL or access token", hide_input=True).strip()
    token, error = extract_token_from_input(raw_input, expected_state=auth_state)
    if error == 'state_mismatch':
        click.echo(click.style("  Invalid auth state. Please run `sentinel login --device` again.", fg='red'))
        return None
    if not token:
        click.echo(click.style("  Could not extract access token from input.", fg='red'))
        return None

    return token_login(token, supabase_url)


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
@click.option('--device', is_flag=True, help='Headless login: paste token after signing in on browser')
@click.option('--supabase-url', envvar='SUPABASE_URL', help='Supabase project URL')
@click.option(
    '--web-url',
    envvar='SENTINEL_WEB_URL',
    help='Website URL for browser auth flow (e.g. https://devops-sentinel.dev)'
)
def login(token: Optional[str], device: bool, supabase_url: Optional[str], web_url: Optional[str]):
    """
    Authenticate with DevOps Sentinel.
    
    Opens browser for secure login. Use --token for CI/CD environments.
    
    Examples:
    
        sentinel login
        
        sentinel login --token YOUR_API_TOKEN
        sentinel login --device
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

    if token and device:
        click.echo(click.style("\nError: Use either --token or --device, not both.", fg='red'))
        return
    
    # Perform login
    if token:
        # Token-based login for CI/CD
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Authenticating with API token...")
        result = token_login(token, supabase_url)
    elif device:
        result = device_login(supabase_url, web_url)
    else:
        # Browser-based login
        result = browser_login(supabase_url, web_url=web_url)
    
    if result:
        # Get user info
        access_token = result.get('access_token', '')
        refresh_token = result.get('refresh_token', '')
        user = result.get('user') or fetch_user_profile(access_token, supabase_url)

        if not access_token:
            click.echo(click.style("\nX Authentication failed: missing access token.", fg='red'))
            return
        if not user or not user.get('id'):
            click.echo(click.style("\nX Authentication failed: could not fetch user profile.", fg='red'))
            click.echo("  Ensure SUPABASE_KEY or SUPABASE_ANON_KEY is configured and try again.")
            return
        
        # Save credentials
        save_credentials(access_token, refresh_token, user)
        
        email = user.get('email', 'Unknown')
        click.echo(f"\n{click.style('OK', fg='green')} Successfully logged in as {email}")
        click.echo(f"  Credentials saved to {CONFIG_DIR}")
        click.echo(f"\n  Next steps:")
        click.echo(f"    sentinel status    - Check configuration")
        click.echo(f"    sentinel monitor <url>   - Start monitoring")
    else:
        click.echo(click.style("\nX Authentication failed.", fg='red'))


@click.command()
def logout():
    """Log out and clear saved credentials."""
    if not is_logged_in():
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Not currently logged in.")
        return
    
    user = get_current_user()
    email = user.get('email', 'Unknown') if user else 'Unknown'
    
    clear_credentials()
    click.echo(f"\n{click.style('OK', fg='green')} Logged out from {email}")
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
    click.echo("-" * 40)
    click.echo(f"  Email: {user.get('email', 'Unknown')}")
    click.echo(f"  ID: {user.get('id', 'Unknown')[:8]}...")
    
    if creds and creds.get('saved_at'):
        import datetime
        saved = datetime.datetime.fromtimestamp(creds['saved_at'])
        click.echo(f"  Authenticated: {saved.strftime('%Y-%m-%d %H:%M')}")
    
    click.echo(f"\n  Config: {CONFIG_DIR}")
    click.echo()

