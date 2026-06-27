import Link from "next/link";
import { ArrowLeft, UserX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function WithdrawalPage() {
  return (
    <div className="space-y-5">
      <section aria-labelledby="withdrawal-heading" className="space-y-3">
        <Button
          asChild
          variant="ghost"
          className="h-9 px-0 text-[#6B4F3A] hover:bg-transparent"
        >
          <Link href="/settings">
            <ArrowLeft aria-hidden="true" size={18} />
            設定へ戻る
          </Link>
        </Button>

        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[#8C715C]">Account</p>
            <h1
              id="withdrawal-heading"
              className="mt-1 text-2xl font-bold leading-tight text-[#2B2926]"
            >
              退会について
            </h1>
            <p className="mt-1 text-sm leading-6 text-[#6F6258]">
              アカウントの退会に関する案内ページです。
            </p>
          </div>

          <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#FFF4F1] text-[#8C3D2F]">
            <UserX aria-hidden="true" size={25} />
          </div>
        </div>
      </section>

      <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">退会機能について</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-6 text-[#6F6258]">
          <p>現在、アプリ上からの退会手続きは準備中です。</p>
          <p>
            退会すると、登録した服やコーデ提案の履歴などのデータが利用できなくなる可能性があります。
          </p>
          <p className="rounded-lg border border-[#F1D0C8] bg-[#FFF7F4] px-4 py-3 text-[#8C3D2F]">
            実際の退会処理はまだ実装していません。
            このページは、退会案内用の仮ページです。
          </p>
          <Button
            type="button"
            variant="outline"
            className="h-11 w-full rounded-lg border-[#E8DED4] text-[#8C3D2F]"
            disabled
          >
            退会機能は準備中です
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
