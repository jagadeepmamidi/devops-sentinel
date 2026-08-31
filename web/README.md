# DevOps Sentinel Web

Public site for the local-first SRE CLI: product story, docs, BYO-Supabase auth helper, and an optional operator console.

## Run

```bash
npm install
npm run dev
```

No hosted Supabase is required for the marketing/docs pages. CLI browser login passes **your** `supabase_url` and `supabase_anon_key` as query parameters to `/cli-auth`.

Public CLI demo endpoints (used by the “Break this endpoint” control):

- `GET /api/demo/ok` — HTTP 200
- `GET /api/demo/fail` — HTTP 503
- `GET /api/demo/live/:id` — HTTP 200 until `POST` breaks it (503 for two minutes); `DELETE` restores it

Optional local operator console:

```env
VITE_API_URL=http://localhost:8000
```

Then run `sentinel serve` and open `/operator/services`.
