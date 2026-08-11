export type IncidentStatus =
	| "detecting"
	| "alerting"
	| "investigating"
	| "resolved";
export type IncidentSeverity = "critical" | "high" | "medium" | "low";

export interface Service {
	id: string;
	name: string;
	url: string;
	check_interval?: number;
	is_active?: boolean;
	[key: string]: unknown;
}
export interface Incident {
	id: string;
	service_id?: string;
	status?: IncidentStatus | string;
	severity?: IncidentSeverity | string;
	[key: string]: unknown;
}
export interface HealthCheck {
	url: string;
	healthy: boolean;
	status?: string;
	status_code?: number;
	response_time_ms?: number;
	[key: string]: unknown;
}
export interface ListResponse<T> {
	count?: number;
	total?: number;
	services?: T[];
	incidents?: T[];
	events?: T[];
}
export interface SentinelClientOptions {
	baseUrl: string;
	token?: string;
	fetch?: typeof globalThis.fetch;
}
