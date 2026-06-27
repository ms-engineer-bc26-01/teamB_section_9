import Link from "next/link";
import { ArrowLeft, Mail } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ContactPage() {
  return (
    <div className="space-y-5">
      <section aria-labelledby="contact-heading" className="space-y-3">
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
            <p className="text-sm font-medium text-[#8C715C]">Support</p>
            <h1
              id="contact-heading"
              className="mt-1 text-2xl font-bold leading-tight text-[#2B2926]"
            >
              お問い合わせ
            </h1>
            <p className="mt-1 text-sm leading-6 text-[#6F6258]">
              アプリの使い方や不具合についてのお問い合わせページです。
            </p>
          </div>

          <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#EAF4F0] text-[#2F6F63]">
            <Mail aria-hidden="true" size={25} />
          </div>
        </div>
      </section>

      <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">お問い合わせについて</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-6 text-[#6F6258]">
          <p>
            現在、お問い合わせフォームは準備中です。
            ご不明点や不具合がある場合は、チーム内で共有してください。
          </p>
          <p>
            今後、このページからお問い合わせ内容を送信できるようにする予定です。
          </p>
          <Button
            type="button"
            variant="outline"
            className="h-11 w-full rounded-lg border-[#E8DED4]"
            disabled
          >
            お問い合わせフォームは準備中です
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
