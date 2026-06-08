"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LogIn } from "lucide-react";

import { supabase } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const redirectParam = searchParams.get("redirect");
  const redirectTo =
    redirectParam &&
    redirectParam.startsWith("/") &&
    !redirectParam.startsWith("//") &&
    !redirectParam.startsWith("/login")
      ? redirectParam
      : "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        setErrorMessage("ログインに失敗しました。入力内容を確認してください。");
        return;
      }

      if (!data.session?.access_token) {
        setErrorMessage("セッション取得に失敗しました。");
        return;
      }

      router.replace(redirectTo);
    } catch {
      setErrorMessage(
        "通信エラーが発生しました。時間をおいて再度お試しください。",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAF8F5] px-6 py-10">
      <div className="mx-auto max-w-sm">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold text-[#6B4F3A]">Climo</h1>
          <p className="mt-3 text-sm text-muted-foreground">
            朝の服選び、もう迷わない。
          </p>
        </div>

        <Card className="border-none shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center justify-center gap-2 text-xl">
              <LogIn aria-hidden="true" className="h-5 w-5" />
              ログイン
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-5">
            <form className="space-y-5" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label
                  htmlFor="email"
                  className="text-sm font-medium text-[#6B4F3A]"
                >
                  メールアドレス
                </label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="example@email.com"
                  required
                />
              </div>

              <div className="space-y-2">
                <label
                  htmlFor="password"
                  className="text-sm font-medium text-[#6B4F3A]"
                >
                  パスワード
                </label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="********"
                  required
                />
              </div>

              {errorMessage && (
                <p
                  role="alert"
                  aria-live="polite"
                  className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
                >
                  {errorMessage}
                </p>
              )}

              <Button
                type="submit"
                className="w-full bg-[#6B4F3A] hover:bg-[#5A412F]"
                disabled={isSubmitting}
              >
                {isSubmitting ? "ログイン中..." : "ログイン"}
              </Button>
            </form>

            <div className="text-center text-sm text-muted-foreground">
              アカウントをお持ちでない方
            </div>

            <Button asChild variant="outline" className="w-full">
              <Link href="/register">新規登録はこちら</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
