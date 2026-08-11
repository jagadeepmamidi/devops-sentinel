import { useState } from "react";
import { Link } from "react-router-dom";
import SiteTopNav from "../components/site/SiteTopNav";
import SiteFooter from "../components/site/SiteFooter";
import "./Landing.css";

const NAV_LINKS = [
  { to: "/cli-auth", label: "CLI Login", className: "primary" },
  { to: "/docs", label: "Docs" },
  { href: "https://pypi.org/project/devops-sentinel-next/", label: "PyPI", external: true },
  { href: "https://github.com/jagadeepmamidi/devops-sentinel", label: "GitHub", external: true },
];

const FOOTER_LINKS = [
  { to: "/terms", label: "Terms" },
  { to: "/privacy", label: "Privacy" },
];

const TERMINAL = String.raw`┌─ SENTINEL / CONTROL PLANE ──────────────────────┐
│  workspace  production              09:41:28 UTC │
├──────────────────────────────────────────────────┤
│  ● api-gateway       HEALTHY       118 ms       │
│  ● checkout-worker   HEALTHY        42 ms       │
│  ! payments-api      DEGRADED      p95 +31%      │
├──────────────────────────────────────────────────┤
│  incident  INC-2048  triage recommended         │
│  evidence  12 events  ·  0 actions executed      │
└──────────────────────────────────────────────────┘`;

export default function Landing() {
  const [copied, setCopied] = useState(false);
  const installCommand = "pip install devops-sentinel-next";

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(installCommand);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="site-page landing-page">
      <a className="site-skip-link" href="#landing-main">Skip to content</a>
      <SiteTopNav links={NAV_LINKS} />

      <main id="landing-main" className="site-main site-container landing-main">
        <section className="landing-hero" aria-labelledby="landing-title">
          <div className="landing-hero-copy">
            <p className="site-label"><span className="landing-live-dot" aria-hidden="true" /> Open-source SRE control plane</p>
            <h1 id="landing-title" className="site-title">Production clarity<br /><span>without the noise.</span></h1>
            <p className="site-text landing-intro">
              DevOps Sentinel turns health signals into evidence-backed incident workflows. Monitor services, give agents safe context, and keep operators in control.
            </p>
            <div className="landing-actions">
              <Link to="/cli-auth" className="site-btn primary">Start from terminal <span aria-hidden="true">↗</span></Link>
              <Link to="/docs" className="site-btn secondary">Read the docs</Link>
            </div>
            <div className="landing-install-pill" role="group" aria-label="Install command">
              <span className="dollar" aria-hidden="true">$</span>
              <code>{installCommand}</code>
              <button className="landing-copy-btn" onClick={copyCommand} type="button" aria-label="Copy install command">{copied ? "Copied" : "Copy"}</button>
              <span className="sr-only" aria-live="polite">{copied ? "Install command copied." : ""}</span>
            </div>
          </div>

          <div className="landing-hero-console site-card" aria-label="Sample Sentinel monitoring console">
            <div className="landing-console-bar"><span className="landing-console-lights" aria-hidden="true"><i /><i /><i /></span><span>sentinel://production</span><span className="landing-console-live">LIVE</span></div>
            <pre>{TERMINAL}</pre>
          </div>
        </section>

        <section className="landing-signal-row" aria-label="Platform capabilities">
          <div><strong>01</strong><span>Observe</span><small>Health, latency, SSL</small></div>
          <div><strong>02</strong><span>Understand</span><small>Timeline, evidence, anomaly</small></div>
          <div><strong>03</strong><span>Respond</span><small>Plans, approvals, postmortems</small></div>
        </section>

        <section className="landing-section" aria-labelledby="workflow-title">
          <div className="landing-section-heading"><p className="site-label">Operating loop</p><h2 id="workflow-title">One system. Every signal.</h2><p className="site-text">A calm workflow for incidents that need speed, context, and a clear audit trail.</p></div>
          <div className="landing-feature-grid">
            <article className="site-card landing-feature-card"><span className="landing-feature-index">A / 01</span><h3>Detect early</h3><p>Run focused endpoint checks with latency, status, SSL, and actionable suggestions.</p><Link to="/docs" className="landing-card-link">Explore monitoring <span aria-hidden="true">→</span></Link></article>
            <article className="site-card landing-feature-card"><span className="landing-feature-index">B / 02</span><h3>Preserve context</h3><p>Keep incident events, investigation notes, response plans, and postmortems together.</p><Link to="/docs" className="landing-card-link">See incident workflow <span aria-hidden="true">→</span></Link></article>
            <article className="site-card landing-feature-card"><span className="landing-feature-index">C / 03</span><h3>Act deliberately</h3><p>Give AI operators read-only context by default. Require explicit approval for destructive work.</p><Link to="/docs" className="landing-card-link">Review safety model <span aria-hidden="true">→</span></Link></article>
          </div>
        </section>

        <section className="landing-bottom-panel site-card" aria-labelledby="mcp-title">
          <div><p className="site-label">Built for people & agents</p><h2 id="mcp-title">Your terminal is the interface.</h2><p className="site-text">Use the CLI, REST API, MCP server, or typed client over one shared operational model.</p></div>
          <div className="landing-stack-list"><span><b>CLI</b> sentinel</span><span><b>MCP</b> agent context</span><span><b>API</b> automation</span></div>
        </section>
      </main>

      <SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel / Next" />
    </div>
  );
}
