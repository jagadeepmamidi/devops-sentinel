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

export default function OperatorIncidents() {
	const [tokenInput, setTokenInput] = useState(() => loadOperatorToken());
	const [incidents, setIncidents] = useState([]);
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
				return operatorFetch("/api/incidents", token);
			})
			.then((payload) => {
				if (!cancelled) {
					setIncidents(payload.incidents || []);
				}
			})
			.catch((err) => {
				if (!cancelled) {
					setError(err.message);
					setIncidents([]);
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
						<h1 className="site-title">Incidents</h1>
						<p className="site-text">
							Browse incident state, severity, and generated postmortems.
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
									setIncidents([]);
								}}
							>
								Clear
							</button>
						</form>
						{error ? (
							<p className="operator-error" role="alert" aria-live="polite">
								{error}
							</p>
						) : null}
					</section>

					<section className="site-card operator-panel">
						<h2>Incident Feed</h2>
						{loading ? <p className="site-text">Loading incidents…</p> : null}
						{!loading && !token ? (
							<p className="operator-empty">Save a token to load incidents.</p>
						) : null}
						{!loading && token && incidents.length === 0 && !error ? (
							<p className="operator-empty">No incidents found for this account.</p>
						) : null}
						{incidents.length > 0 ? (
							<table className="operator-table">
								<thead>
									<tr>
										<th>Service</th>
										<th>Status</th>
										<th>Severity</th>
										<th>Detected</th>
									</tr>
								</thead>
								<tbody>
									{incidents.map((incident) => (
										<tr key={incident.id}>
											<td>
												<Link
													className="operator-link"
													to={`/operator/incidents/${incident.id}`}
												>
													{incident.service_name || incident.service_id}
												</Link>
												<div className="site-text">
													{incident.error_message || "No error summary recorded."}
												</div>
											</td>
											<td>
												<span
													className={`operator-status ${incident.status || "detecting"}`}
												>
													{incident.status}
												</span>
											</td>
											<td>{incident.severity}</td>
											<td>{incident.detected_at || "Unknown"}</td>
										</tr>
									))}
								</tbody>
							</table>
						) : null}
					</section>
				</div>
			</main>

			<SiteFooter links={FOOTER_LINKS} text="DevOps Sentinel incident console" />
		</div>
	);
}
