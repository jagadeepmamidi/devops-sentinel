# @devops-sentinel/client

Typed Node.js client for DevOps Sentinel HTTP API.

```ts
import { SentinelClient } from "@devops-sentinel/client";
const sentinel = new SentinelClient({ baseUrl: "https://your-sentinel.example.com", token: process.env.SENTINEL_TOKEN });
const result = await sentinel.healthCheck("https://api.example.com/health");
```

Supports health checks, incident listing, incident timelines, and postmortem generation. API remains source of truth; package does not duplicate monitoring logic.

Requires Node.js 18+.
