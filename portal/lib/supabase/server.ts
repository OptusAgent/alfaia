import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

// Client server-side (Server Components, Route Handlers, Server Actions).
// Nunca usa a service key aqui — sempre a anon key, sob RLS (coding-standards.md §3).
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            // Chamado de um Server Component sem permissão de escrita de cookie —
            // o middleware já cuida do refresh de sessão nesse caso.
          }
        },
      },
    },
  );
}
