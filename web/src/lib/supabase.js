import { createClient } from '@supabase/supabase-js'

export function createSupabaseClient(url, key) {
  const supabaseUrl = (url || '').trim()
  const supabaseKey = (key || '').trim()
  if (!supabaseUrl || !supabaseKey) return null
  return createClient(supabaseUrl, supabaseKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  })
}

export const supabase = createSupabaseClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)
