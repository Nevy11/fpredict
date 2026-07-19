import { createClient } from '@supabase/supabase-js'
import WebSocket from 'isomorphic-ws'

const supabaseUrl = 'https://example.com'
const supabaseAnonKey = 'key'
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  realtime: { transport: WebSocket }
})
