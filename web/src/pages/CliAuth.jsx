import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import SiteTopNav from "../components/site/SiteTopNav";
import SiteFooter from "../components/site/SiteFooter";
import { supabase } from "../lib/supabase";
import "./CliAuth.css";

const NAV_LINKS = [
  { to: "/docs", label: "Docs" },
  { to: "/", label: "Home" },
];

const FOOTER_LINKS = [
  { to: "/terms", label: "Terms" },
  { to: "/privacy", label: "Privacy" },
];

export default function CliAuth() {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState("openrouter");
  const [session, setSession] = useState(null);
  const [emailSent, setEmailSent] = useState(false);
  const [showKeyNudge, setShowKeyNudge] = useState(false);
  const [savingKey, setSavingKey] = useState(false);
  const [keySaved, setKeySaved] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const redirectUri =
    searchParams.get("redirect_uri") || `${window.location.origin}/cli-auth`;
  const state = searchParams.get("state") || "";
  const apiBase = import.meta.env.VITE_API_URL || "";
  const hasConfig = Boolean(supabase);

  useEffect(() => {
    if (!supabase) return undefined;
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (active && data.session) {
        setSession(data.session);
        setShowKeyNudge(true);
      }
    });
    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, nextSession) => {
        setSession(nextSession);
        if (nextSession) setShowKeyNudge(true);
      },
    );
    return () => {
      active = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  async function signInWithProvider(nextProvider) {
    setError("");
    if (!supabase) {
      setError(
        "Auth is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.",
      );
      return;
    }
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider: nextProvider,
      options: {
        redirectTo: redirectUri,
        queryParams: state ? { state } : undefined,
      },
    });
    if (authError) setError(authError.message);
  }

  async function sendMagicLink(event) {
    event.preventDefault();
    setError("");
    if (!supabase) {
      setError(
        "Auth is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.",
      );
      return;
    }
    const { error: authError } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: redirectUri },
    });
    if (authError) setError(authError.message);
    else setEmailSent(true);
  }

  async function saveApiKey(event) {
    event.preventDefault();
    if (!session?.access_token || !apiKey.trim()) return;
    setSavingKey(true);
    setError("");
    try {
      const response = await fetch(`${apiBase}/api/setup/ai/key`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ provider, api_key: apiKey.trim() }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok)
        throw new Error(payload.detail || "Could not save API key.");
      setApiKey("");
      setKeySaved(true);
      setShowKeyNudge(false);
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setSavingKey(false);
    }
  }

  async function copyDeviceCommand() {
    try {
      await navigator.clipboard.writeText("sentinel login --device");
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="site-page cli-auth-page">
      <a className="site-skip-link" href="#auth-main">
        Skip to content
      </a>
      <SiteTopNav links={NAV_LINKS} />
      <main id="auth-main" className="site-main site-container cli-auth-main">
        <section className="site-card cli-auth-panel">
          <p className="site-label">Secure access / OAuth 2.0</p>
          <h1 className="site-title">Sign in to continue in terminal</h1>
          <p className="site-text">
            Browser authentication returns a bearer access token to Sentinel.
            Session refresh and storage stay with Supabase Auth.
          </p>

          <div className="site-btn-row cli-auth-provider-row">
            <button
              className="site-btn primary"
              type="button"
              onClick={() => signInWithProvider("google")}
              disabled={!hasConfig}
            >
              Continue with Google
            </button>
            <button
              className="site-btn secondary"
              type="button"
              onClick={() => signInWithProvider("github")}
              disabled={!hasConfig}
            >
              Continue with GitHub
            </button>
          </div>

          <form className="cli-auth-email-form" onSubmit={sendMagicLink}>
            <label htmlFor="auth-email">Email magic link</label>
            <div className="cli-auth-email-row">
              <input
                id="auth-email"
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@company.com"
              />
              <button
                className="site-btn secondary"
                type="submit"
                disabled={!hasConfig}
              >
                Send link
              </button>
            </div>
          </form>
          {emailSent && (
            <p className="cli-auth-success" role="status">
              Check email for secure sign-in link.
            </p>
          )}
          {error && (
            <p className="cli-auth-error" role="alert">
              {error}
            </p>
          )}
          {keySaved && (
            <p className="cli-auth-success" role="status">
              AI provider key saved securely.
            </p>
          )}
          {!hasConfig && (
            <div className="cli-auth-warning">
              Set <code className="site-inline-code">VITE_SUPABASE_URL</code>{" "}
              and{" "}
              <code className="site-inline-code">VITE_SUPABASE_ANON_KEY</code>{" "}
              before enabling auth.
            </div>
          )}

          {session && (
            <div className="cli-auth-session">
              <span className="cli-auth-dot" /> Signed in as{" "}
              {session.user.email}
            </div>
          )}
        </section>

        <aside className="site-card soft cli-auth-terminal">
          <h2>Terminal fallback</h2>
          <pre className="site-code-block">{`$ sentinel login
$ sentinel services add my-api https://api.example.com/health
$ sentinel monitor https://api.example.com/health`}</pre>
          <p className="site-text">
            If browser callback is blocked, use device flow:
          </p>
          <button
            className="site-btn secondary cli-auth-copy-btn"
            onClick={copyDeviceCommand}
            type="button"
          >
            {copied ? "Copied" : "Copy: sentinel login --device"}
          </button>
          <span className="sr-only" aria-live="polite">
            {copied ? "Device login command copied." : ""}
          </span>
        </aside>
      </main>

      {showKeyNudge && session && (
        <div className="cli-auth-modal-backdrop" role="presentation">
          <section
            className="site-card cli-auth-key-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="api-key-title"
          >
            <p className="site-label">One last setup step</p>
            <h2 id="api-key-title">Connect an AI provider?</h2>
            <p className="site-text">
              Sentinel agents use your provider key for explanations and
              postmortems. Key is encrypted server-side and never returned to
              browser.
            </p>
            <form onSubmit={saveApiKey}>
              <label htmlFor="provider">Provider</label>
              <select
                id="provider"
                value={provider}
                onChange={(event) => setProvider(event.target.value)}
              >
                <option value="openrouter">OpenRouter</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
              </select>
              <label htmlFor="api-key">API key</label>
              <input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="sk-..."
                autoComplete="off"
                required
              />
              <div className="site-btn-row">
                <button
                  className="site-btn primary"
                  type="submit"
                  disabled={savingKey}
                >
                  {savingKey ? "Saving..." : "Save key"}
                </button>
                <button
                  className="site-btn secondary"
                  type="button"
                  onClick={() => setShowKeyNudge(false)}
                >
                  Skip for now
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel auth" />
    </div>
  );
}
