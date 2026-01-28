# DevOps Sentinel Web Dashboard

React + Vite application with Supabase authentication.

## Setup

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure Supabase**
   
   Create `.env` file:
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

## Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com)

2. Run the schema migration at `../supabase/schema.sql` in the SQL Editor

3. Enable authentication providers:
   - Dashboard → Authentication → Providers
   - Enable: Email, Google, GitHub

4. Configure OAuth:
   - Google: Create OAuth credentials at Google Cloud Console
   - GitHub: Create OAuth app at GitHub Developer Settings

5. Set redirect URLs:
   - Add `http://localhost:5173` for local development
   - Add your production URL when deploying

## Deploy to Vercel

```bash
npx vercel
```

Set environment variables in Vercel dashboard:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

## Project Structure

```
src/
├── components/     # Reusable components
│   └── Navbar.jsx
├── contexts/       # React contexts
│   └── AuthContext.jsx
├── lib/            # Utilities
│   └── supabase.js
└── pages/          # Page components
    ├── Landing.jsx
    ├── Auth.jsx
    ├── Dashboard.jsx
    ├── Projects.jsx
    ├── Incidents.jsx
    └── Postmortems.jsx
```
