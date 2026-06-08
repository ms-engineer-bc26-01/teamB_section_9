import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from "@/components/ui/drawer";
import { Home, Shirt, User } from "lucide-react";

import { ClothingCard } from "@/components/clothes/ClothingCard";
import { OutfitSummaryCard } from "@/components/outfit/OutfitSummaryCard";

export default function UiSamplePage() {
  return (
    <main className="min-h-screen bg-[#FAF8F5] px-4 py-6 text-[#2B2926]">
      <div className="mx-auto max-w-[390px] space-y-6">
        <header className="space-y-1">
          <p className="text-sm text-[#8C715C]">Climo UI Sample</p>
          <h1 className="text-2xl font-bold">共通UIサンプル</h1>
          <p className="text-sm text-muted-foreground">
            shadcn/ui の基本コンポーネント確認ページです。
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Button / Badge</CardTitle>
            <CardDescription>主要アクションと状態表示</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Button>今日のコーデを見る</Button>
              <Button variant="outline">服を登録</Button>
            </div>
            <div className="flex gap-2">
              <Badge>business</Badge>
              <Badge variant="secondary">spring</Badge>
              <Badge variant="outline">favorite</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Input</CardTitle>
            <CardDescription>フォーム入力の確認</CardDescription>
          </CardHeader>
          <CardContent>
            <Input placeholder="例：白いブラウス" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Select</CardTitle>
            <CardDescription>TPO 選択の想定</CardDescription>
          </CardHeader>
          <CardContent>
            <Select>
              <SelectTrigger>
                <SelectValue placeholder="シーンを選択" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="business">仕事</SelectItem>
                <SelectItem value="casual">カジュアル</SelectItem>
                <SelectItem value="formal">フォーマル</SelectItem>
                <SelectItem value="leisure">お出かけ</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Dialog / Drawer</CardTitle>
            <CardDescription>モーダル系UIの確認</CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="outline">Dialogを開く</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>コーデ提案</DialogTitle>
                  <DialogDescription>
                    今日の天気に合わせた提案を表示します。
                  </DialogDescription>
                </DialogHeader>
              </DialogContent>
            </Dialog>

            <Drawer>
              <DrawerTrigger asChild>
                <Button variant="outline">Drawerを開く</Button>
              </DrawerTrigger>
              <DrawerContent>
                <DrawerHeader>
                  <DrawerTitle>服の詳細</DrawerTitle>
                  <DrawerDescription>
                    登録済みアイテムの情報を表示します。
                  </DrawerDescription>
                </DrawerHeader>
              </DrawerContent>
            </Drawer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Bottom Navigation</CardTitle>
            <CardDescription>Climo用の仮ナビゲーション</CardDescription>
          </CardHeader>
          <CardContent>
            <nav className="grid grid-cols-3 rounded-2xl border bg-white p-2 shadow-sm">
              <button className="flex flex-col items-center gap-1 rounded-xl px-3 py-2 text-xs text-[#6B4F3A]">
                <Home size={20} />
                Home
              </button>
              <button className="flex flex-col items-center gap-1 rounded-xl px-3 py-2 text-xs text-muted-foreground">
                <Shirt size={20} />
                Closet
              </button>
              <button className="flex flex-col items-center gap-1 rounded-xl px-3 py-2 text-xs text-muted-foreground">
                <User size={20} />
                My
              </button>
            </nav>
          </CardContent>
        </Card>

        <section className="space-y-4">
          <h2 className="text-xl font-semibold">
            ClothingCard
          </h2>

          <ClothingCard
            name="白シャツ"
            category="tops"
            color="white"
            season={["spring", "summer"]}
            imageUrl={null}
            isFavorite
          />
        </section>
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">
            OutfitSummaryCard
          </h2>

          <OutfitSummaryCard
            tpo="business"
            weatherSummary="晴れ 22℃"
            comment="朝晩の寒暖差に対応できる軽めの羽織りを取り入れたコーデです。"
            isFavorite
          />
        </section>
      </div>
    </main>
  );
}
