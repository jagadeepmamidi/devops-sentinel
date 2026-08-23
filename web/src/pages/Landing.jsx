import { useState } from "react";
import { Link } from "react-router-dom";
import SiteTopNav from "../components/site/SiteTopNav";
import SiteFooter from "../components/site/SiteFooter";
import BrandOrb from "../components/BrandOrb";
import "./Landing.css";

const NAV_LINKS = [
	{ to: "/docs", label: "Docs" },
	{
		href: "https://pypi.org/project/devops-sentinel-next/",
		label: "PyPI",
		external: true,
	},
	{
		href: "https://github.com/jagadeepmamidi/devops-sentinel",
		label: "GitHub",
		external: true,
	},
	{ to: "/cli-auth", label: "Open console", className: "primary" },
];

const FOOTER_LINKS = [
	{ to: "/terms", label: "Terms" },
	{ to: "/privacy", label: "Privacy" },
];

const INSTALL_COMMAND = "pip install devops-sentinel-next";

function ProductPreview() {
	return (
		<div
			className="product-preview site-card"
			aria-label="DevOps Sentinel product preview"
		>
			<div className="product-window-bar">
				<span className="window-dots" aria-hidden="true">
					<i />
					<i />
					<i />
				</span>
				<span className="window-breadcrumb">sentinel / production / overview</span>
				<span className="window-secure">● connected</span>
			</div>
			<div className="product-window-body">
				<aside className="product-sidebar" aria-hidden="true">
					<span className="product-sidebar-label">Workspace</span>
					<strong>Production</strong>
					<span className="product-nav-active">Overview</span>
					<span>
						Services <em>8</em>
					</span>
					<span>
						Incidents <em className="alert-count">2</em>
					</span>
					<span>Postmortems</span>
					<span className="product-sidebar-label product-sidebar-bottom">
						Workspace
					</span>
					<span>MCP access</span>
					<span>Settings</span>
				</aside>
				<div className="product-content">
					<div className="product-content-heading">
						<div>
							<span className="product-kicker">Overview / last 24 hours</span>
							<h2>System health</h2>
						</div>
						<span className="product-time">Updated 12s ago</span>
					</div>
					<div className="product-stats">
						<div>
							<span>Availability</span>
							<strong>99.98%</strong>
							<small className="positive">↑ 0.04%</small>
						</div>
						<div>
							<span>Active incidents</span>
							<strong>02</strong>
							<small className="warning">Needs attention</small>
						</div>
						<div>
							<span>p95 latency</span>
							<strong>184ms</strong>
							<small className="positive">↓ 12ms</small>
						</div>
					</div>
					<div className="product-grid-row">
						<div className="product-chart">
							<div className="product-module-heading">
								<strong>Request health</strong>
								<span>24h ▾</span>
							</div>
							<div className="chart-area" aria-hidden="true">
								<i />
								<i />
								<i />
								<i />
								<i />
								<i />
								<i />
								<i />
								<i />
								<i />
								<b />
								<b />
							</div>
							<div className="chart-labels">
								<span>00:00</span>
								<span>06:00</span>
								<span>12:00</span>
								<span>18:00</span>
								<span>Now</span>
							</div>
						</div>
						<div className="product-incidents">
							<div className="product-module-heading">
								<strong>Attention needed</strong>
								<Link to="/docs">View all</Link>
							</div>
							<div className="incident-row">
								<span className="incident-severity critical">!</span>
								<div>
									<strong>Payments API latency</strong>
									<small>Investigating · 8 min ago</small>
								</div>
								<span className="incident-arrow">↗</span>
							</div>
							<div className="incident-row">
								<span className="incident-severity warning">!</span>
								<div>
									<strong>Checkout worker queue</strong>
									<small>Degraded · 21 min ago</small>
								</div>
								<span className="incident-arrow">↗</span>
							</div>
						</div>
					</div>
					<div className="product-services">
						<div className="product-module-heading">
							<strong>Services</strong>
							<span>8 monitored</span>
						</div>
						<div className="service-strip">
							<span>
								<i className="healthy" />
								api-gateway <b>118ms</b>
							</span>
							<span>
								<i className="healthy" />
								checkout-worker <b>42ms</b>
							</span>
							<span>
								<i className="degraded" />
								payments-api <b>+31%</b>
							</span>
							<span>
								<i className="healthy" />
								web-console <b>86ms</b>
							</span>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}

export default function Landing() {
	const [copied, setCopied] = useState(false);

	async function copyCommand() {
		try {
			await navigator.clipboard.writeText(INSTALL_COMMAND);
			setCopied(true);
			window.setTimeout(() => setCopied(false), 1800);
		} catch {
			setCopied(false);
		}
	}

	return (
		<div className="site-page landing-page">
			<a className="site-skip-link" href="#landing-main">
				Skip to content
			</a>
			<SiteTopNav links={NAV_LINKS} />
			<main id="landing-main" className="site-main site-container landing-main">
				<section className="landing-hero" aria-labelledby="landing-title">
					<div className="landing-orb-stage">
						<BrandOrb size="large" label="Animated DevOps Sentinel logo orb" />
						<span className="landing-orb-status">● agent signal / ready</span>
					</div>
					<p className="landing-eyebrow">
						<span aria-hidden="true">✳</span> DevOps Sentinel Next{" "}
						<b>Now available on PyPI</b>
					</p>
					<h1 id="landing-title">
						Resolve production issues
						<br />
						<em>before they become incidents.</em>
					</h1>
					<p className="landing-hero-copy">
						Open-source monitoring and incident operations for teams that want fast
						signal, durable context, and safe automation.
					</p>
					<div className="landing-hero-actions">
						<Link to="/cli-auth" className="site-btn primary">
							Start monitoring <span aria-hidden="true">↗</span>
						</Link>
						<Link to="/docs" className="site-btn secondary">
							Read documentation
						</Link>
					</div>
					<div className="landing-install" role="group" aria-label="Install command">
						<code>
							<span>$</span> {INSTALL_COMMAND}
						</code>
						<button type="button" onClick={copyCommand}>
							{copied ? "Copied" : "Copy"}
						</button>
						<span className="sr-only" aria-live="polite">
							{copied ? "Install command copied." : ""}
						</span>
					</div>
				</section>

				<section
					className="landing-preview-section"
					aria-labelledby="preview-title"
				>
					<div className="landing-section-intro">
						<span className="site-label">One view, full context</span>
						<h2 id="preview-title">Your production picture, without the noise.</h2>
						<p className="site-text">
							Health checks, service state, active incidents, and evidence-backed next
							steps in one operational surface.
						</p>
					</div>
					<ProductPreview />
				</section>

				<section
					className="landing-capabilities"
					aria-labelledby="capabilities-title"
				>
					<div className="landing-section-intro">
						<span className="site-label">Designed for response</span>
						<h2 id="capabilities-title">Everything after the alert.</h2>
					</div>
					<div className="capability-grid">
						<article className="capability-card">
							<span className="capability-number">01</span>
							<h3>Find the signal</h3>
							<p>
								Check one endpoint or your whole service surface with latency, SSL, and
								failure evidence.
							</p>
							<Link to="/docs">
								Explore health checks <span aria-hidden="true">→</span>
							</Link>
						</article>
						<article className="capability-card capability-card-featured">
							<span className="capability-number">02</span>
							<h3>Build the timeline</h3>
							<p>
								Keep detection, investigation, response, and resolution events attached
								to every incident.
							</p>
							<div className="mini-timeline" aria-hidden="true">
								<span>
									<i />
									Detected <b>09:12</b>
								</span>
								<span>
									<i />
									Investigating <b>09:16</b>
								</span>
								<span>
									<i />
									Plan ready <b>09:20</b>
								</span>
							</div>
						</article>
						<article className="capability-card">
							<span className="capability-number">03</span>
							<h3>Give agents guardrails</h3>
							<p>
								Expose operational context through MCP while keeping destructive
								remediation behind approval.
							</p>
							<Link to="/docs">
								Read the safety model <span aria-hidden="true">→</span>
							</Link>
						</article>
					</div>
				</section>

				<section
					className="landing-final-cta site-card"
					aria-labelledby="final-cta-title"
				>
					<div>
						<span className="site-label">Start with one command</span>
						<h2 id="final-cta-title">
							Make your next incident
							<br />
							less surprising.
						</h2>
					</div>
					<div className="landing-final-actions">
						<Link to="/cli-auth" className="site-btn primary">
							Open console ↗
						</Link>
						<a
							className="site-btn secondary"
							href="https://github.com/jagadeepmamidi/devops-sentinel"
							target="_blank"
							rel="noreferrer"
						>
							View on GitHub
						</a>
					</div>
				</section>
			</main>
			<SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel / Next" />
		</div>
	);
}
