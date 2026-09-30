import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabasePublishableKey = process.env.REACT_APP_SUPABASE_PUBLISHABLE_KEY;

if (!supabaseUrl || !supabasePublishableKey) {
  throw new Error('Supabase environment variables are missing.');
}

export const supabase = createClient(
  supabaseUrl,
  supabasePublishableKey
);
export async function testSupabaseConnection() {
  const { error } = await supabase.auth.getSession();

  if (error) {
    console.error('Supabase connection error:', error);
    return false;
  }

  return true;
}


