"use client";

import { useEffect } from "react";
import { supabase } from "@/lib/auth";
import { useAuthStore } from "@/stores/auth-store";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const setAuth = useAuthStore((state) => state.setAuth);
  const clearAuth = useAuthStore((state) => state.clearAuth);

  useEffect(() => {
    let mounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      setAuth(data.session ?? null);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setAuth(session);
        return;
      }
      clearAuth();
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [setAuth, clearAuth]);

  return children;
}
