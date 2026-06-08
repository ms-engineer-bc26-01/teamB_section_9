import { RequireAuth } from "@/components/auth/RequireAuth";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
