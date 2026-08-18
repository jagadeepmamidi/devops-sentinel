import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import SiteFooter from "../components/site/SiteFooter";
import SiteTopNav from "../components/site/SiteTopNav";
import {
	loadOperatorToken,
	operatorFetch,
	saveOperatorToken,
} from "../lib/operatorApi";
import "./Operator.css";

const NAV_LINKS = [
	{ to: "/operator/services", label: "Services" },
	{ to: "/operator/incidents", label: "Incidents" },
	{ to: "/docs", label: "Docs" },
];

const FOOTER_LINKS = [
	{ to: "/privacy", label: "Privacy" },
	{ to: "/terms", label: "Terms" },
];

export default function OperatorServices() {
	const [tokenInput, setTokenInput] = useState(() => loadOperatorToken());
	const [services, setServices] = useState([]);
	const [error, setError] = useState("");
	const [loading, setLoading] = useState(false);

	const token = loadOperatorToken();

	useEffect(() => {
		if (!token) {
			return;
		}

		let cancelled = false;

		Promise.resolve()
			.then(() => {
				if (!cancelled) {
					setLoading(true);
					setError("");
				}
				return operatorFetch("/api/services", token);
			})
			.then((payload) => {
				if (!cancelled) {
					setServices(payload.services || []);
				}
			})
			.catch((err) => {
				if (!cancelled) {
					setError(err.message);
					setServices([]);
				}
			})
			.finally(() => {
				if (!cancelled) {
					setLoading(false);
				}
			});

		return () => {
			cancelled = true;
		};
	}, [token]);

	function handleSaveToken(event) {
		event.preventDefault();
		saveOperatorToken(tokenInput.trim());
		setError("");
	}

	return (
		<div className="site-page">
			<a className="site-skip-link" href="#operator-main">
				Skip to content
			</a>
			<SiteTopNav links={NAV_LINKS} brandTo="/" />

			<main id="operator-main" className="site-main site-container operator-main">
				<div className="operator-stack">
					<section className="site-card operator-panel">
						<p className="site-label">Operator Console</p>
						<h1 className="site-title">Services</h1>
						<p className="site-text">
							Paste a bearer token from your authenticated API session to inspect
							monitored services.
						</p>

						<form className="operator-token-form" onSubmit={handleSaveToken}>
							<input
								type="password"
								value={tokenInput}
								onChange={(event) => setTokenInput(event.target.value)}
								placeholder="Paste bearer token…"
								aria-label="Bearer token"
								name="token"
								autoComplete="off"
							/>
							<button className="site-btn primary" type="submit">
								Save token
							</button>
							<button
								className="site-btn secondary"
								type="button"
								onClick={() => {
									saveOperatorToken("");
									setTokenInput("");
									setServices([]);
								}}
							>
								Clear
							</button>
						</form>
						<p className="operator-note site-text">
							Use the same token you use for authenticated `/api/*` requests.
						</p>
						{error ? (
							<p className="operator-error" role="alert" aria-live="polite">
								{error}
							</p>
						) : null}
					</section>

					<section className="site-card operator-panel">
						<h2>Registered Services</h2>
						{loading ? <p className="site-text">Loading services…</p> : null}
						{!loading && !token ? (
							<p className="operator-empty">Save a token to load services.</p>
						) : null}
						{!loading && token && services.length === 0 && !error ? (
							<p className="operator-empty">No services found for this account.</p>
						) : null}
						{services.length > 0 ? (
							<table className="operator-table">
								<thead>
									<tr>
										<th>Name</th>
										<th>Status</th>
										<th>Check Interval</th>
										<th>Last Check</th>
									</tr>
								</thead>
								<tbody>
									{services.map((service) => (
										<tr key={service.id}>
											<td>
												<strong>{service.name}</strong>
												<div>
													<a
														className="operator-link"
														href={service.url}
														target="_blank"
														rel="noreferrer"
													>
														{service.url}
													</a>
												</div>
											</td>
											<td>
												<span
													className={`operator-status ${service.last_status || "unknown"}`}
												>
													{service.last_status || "unknown"}
												</span>
											</td>
											<td>{service.check_interval}s</td>
											<td>{service.last_checked_at || "Never"}</td>
										</tr>
									))}
								</tbody>
							</table>
						) : null}
					</section>

					<section className="site-card soft operator-panel">
						<h3>Next step</h3>
						<p className="site-text">
							Review active and historical incidents in the{" "}
							<Link className="operator-link" to="/operator/incidents">
								incidents console
							</Link>
							.
						</p>
					</section>
				</div>
			</main>

			<SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel operator console" />
		</div>
	);
}
