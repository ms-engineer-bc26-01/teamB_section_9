// frontend/src/stores/auth-store.ts
import { create } from "zustand";
import type { Session, User } from "@supabase/supabase-js";

type AuthState = {
  user: User | null;
  session: Session | null;
  isInitialized: boolean;
  setAuth: (session: Session | null) => void;
  clearAuth: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  session: null,
  isInitialized: false,
  setAuth: (session) =>
    set({
      session,
      user: session?.user ?? null,
      isInitialized: true,
    }),
  clearAuth: () =>
    set({
      session: null,
      user: null,
      isInitialized: true,
    }),
}));
