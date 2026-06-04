import Link from "next/link";
import { LockKeyhole, LogIn, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
  return (
    <div className="flex min-h-[calc(100vh-7rem)] flex-col justify-center space-y-5">
      <section className="space-y-2">
        <p className="text-sm font-medium text-[#8C715C]">Climo</p>
        <h1 className="text-2xl font-bold leading-tight text-[#2B2926]">
          ログイン
        </h1>
        <p className="text-sm leading-6 text-[#6F6258]">
          手持ちの服とお気に入りのコーデを保存して、毎日の服選びを続けましょう。
        </p>
      </section>

      <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <LogIn size={18} className="text-[#6B4F3A]" />
            アカウント情報
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form className="space-y-4">
            <label className="block space-y-2">
              <span className="flex items-center gap-2 text-sm font-medium text-[#4B3A2F]">
                <Mail size={16} />
                メールアドレス
              </span>
              <Input
                type="email"
                placeholder="example@climo.app"
                autoComplete="email"
                className="h-11 rounded-lg border-[#D9C9BA] bg-white"
              />
            </label>

            <label className="block space-y-2">
              <span className="flex items-center gap-2 text-sm font-medium text-[#4B3A2F]">
                <LockKeyhole size={16} />
                パスワード
              </span>
              <Input
                type="password"
                placeholder="パスワードを入力"
                autoComplete="current-password"
                className="h-11 rounded-lg border-[#D9C9BA] bg-white"
              />
            </label>

            <Button className="h-11 w-full bg-[#5A4333] text-white hover:bg-[#4A372A]">
              ログイン
            </Button>
          </form>

          <div className="mt-4 flex items-center justify-between gap-3 text-sm">
            <Link href="/" className="font-medium text-[#6B4F3A] underline-offset-4 hover:underline">
              ホームへ戻る
            </Link>
            <Link href="/signup" className="text-[#8C715C] underline-offset-4 hover:underline">
              新規登録
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
