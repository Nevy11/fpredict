import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL ?? 'https://agojvvfjajkkpqohehcm.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY ?? 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnb2p2dmZqYWpra3Bxb2hlaGNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEzNDkyMzEsImV4cCI6MjA5NjkyNTIzMX0.VVKkTvlGRvQWKhOo_GzReyN9zUaw0J6CKm3voY-V6vU'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
