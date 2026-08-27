# DevOps Sentinel Web

Public site for the local-first SRE CLI: product story, docs, BYO-Supabase auth helper, and an optional operator console.

## Run

```bash
npm install
npm run dev
```

No hosted Supabase is required for the marketing/docs pages. CLI browser login passes **your** `supabase_url` and `supabase_anon_key` as query parameters to `/cli-auth`.

Optional local operator console:

```env
VITE_API_URL=http://localhost:8000
```

Then run `sentinel serve` and open `/operator/services`.
