import Link from "next/link";
import { ArrowLeft, Camera, Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

const seasons = [
    { label: "春", value: "spring" },
    { label: "夏", value: "summer" },
    { label: "秋", value: "autumn" },
    { label: "冬", value: "winter" },
    { label: "通年", value: "all" },
];

const tpoTags = [
    { label: "カジュアル", value: "casual" },
    { label: "オフィス", value: "business" },
    { label: "フォーマル", value: "formal" },
    { label: "セレモニー", value: "ceremony" },
    { label: "レジャー", value: "leisure" },
];

export default function ClothesRegisterPage() {
    return (
        <main className="min-h-screen bg-[#FAF8F5] px-4 py-6 text-[#222222]">
            <div className="mx-auto flex w-full max-w-[390px] flex-col gap-6">
                <header className="flex items-center gap-3">
                    <Button asChild variant="ghost" size="icon" aria-label="服一覧に戻る">
                        <Link href="/clothes">
                            <ArrowLeft className="h-5 w-5" aria-hidden="true" />
                        </Link>
                    </Button>

                    <div>
                        <p className="text-xs text-[#8C715C]">Closet</p>
                        <h1 className="text-xl font-semibold tracking-tight">服を登録</h1>
                    </div>
                </header>

                <Card className="border-[#E8DED4] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-base">写真</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <button
                            type="button"
                            className="flex aspect-[4/3] w-full flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-[#D8CABE] bg-[#FAF8F5] text-sm text-[#6B4F3A]"
                            aria-label="服の写真を追加する"
                        >
                            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white">
                                <Camera className="h-6 w-6" aria-hidden="true" />
                            </span>
                            <span>写真を追加</span>
                            <span className="text-xs text-[#8C715C]">
                                画像登録・AI判定は後続PRで接続
                            </span>
                        </button>
                    </CardContent>
                </Card>

                <Card className="border-[#E8DED4] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-base">基本情報</CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-4">
                        <div className="flex flex-col gap-2">
                            <label htmlFor="name" className="text-sm font-medium">
                                服の名前 <span className="text-[#8C715C]">*</span>
                            </label>
                            <Input
                                id="name"
                                name="name"
                                placeholder="例：白のリネンシャツ"
                                className="bg-white"
                            />
                        </div>

                        <div className="flex flex-col gap-2">
                            <label htmlFor="category" className="text-sm font-medium">
                                カテゴリ <span className="text-[#8C715C]">*</span>
                            </label>
                            <Select>
                                <SelectTrigger id="category" className="bg-white">
                                    <SelectValue placeholder="カテゴリを選択" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="tops">トップス</SelectItem>
                                    <SelectItem value="bottoms">ボトムス</SelectItem>
                                    <SelectItem value="outer">アウター</SelectItem>
                                    <SelectItem value="shoes">靴</SelectItem>
                                    <SelectItem value="bag">バッグ</SelectItem>
                                    <SelectItem value="accessory">アクセサリー</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="flex flex-col gap-2">
                                <label htmlFor="color" className="text-sm font-medium">
                                    色
                                </label>
                                <Input
                                    id="color"
                                    name="color"
                                    placeholder="例：白"
                                    className="bg-white"
                                />
                            </div>

                            <div className="flex flex-col gap-2">
                                <label htmlFor="size" className="text-sm font-medium">
                                    サイズ
                                </label>
                                <Input
                                    id="size"
                                    name="size"
                                    placeholder="例：M"
                                    className="bg-white"
                                />
                            </div>
                        </div>

                        <div className="flex flex-col gap-2">
                            <label htmlFor="pattern" className="text-sm font-medium">
                                柄
                            </label>
                            <Select>
                                <SelectTrigger id="pattern" className="bg-white">
                                    <SelectValue placeholder="柄を選択" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="solid">無地</SelectItem>
                                    <SelectItem value="stripe">ストライプ</SelectItem>
                                    <SelectItem value="check">チェック</SelectItem>
                                    <SelectItem value="dot">ドット</SelectItem>
                                    <SelectItem value="floral">花柄</SelectItem>
                                    <SelectItem value="other">その他</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-[#E8DED4] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-base">着用シーン</CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-5">
                        <div className="flex flex-col gap-2">
                            <p className="text-sm font-medium">
                                季節 <span className="text-[#8C715C]">*</span>
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {seasons.map((season) => (
                                    <Badge
                                        key={season.value}
                                        variant="outline"
                                        className="rounded-full border-[#D8CABE] px-3 py-1 text-[#6B4F3A]"
                                    >
                                        {season.label}
                                    </Badge>
                                ))}
                            </div>
                            <p className="text-xs text-[#8C715C]">
                                複数選択の状態管理は後続PRで実装
                            </p>
                        </div>

                        <div className="flex flex-col gap-2">
                            <p className="text-sm font-medium">TPO</p>
                            <div className="flex flex-wrap gap-2">
                                {tpoTags.map((tag) => (
                                    <Badge
                                        key={tag.value}
                                        variant="outline"
                                        className="rounded-full border-[#D8CABE] px-3 py-1 text-[#6B4F3A]"
                                    >
                                        {tag.label}
                                    </Badge>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card className="border-[#E8DED4] bg-white shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-base">メモ</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <label htmlFor="memo" className="sr-only">
                            メモ
                        </label>
                        <textarea
                            id="memo"
                            name="memo"
                            maxLength={200}
                            placeholder="素材感、着心地、合わせたい服など"
                            className="min-h-28 w-full resize-none rounded-md border border-input bg-white px-3 py-2 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
                        />
                        <p className="mt-2 text-xs text-[#8C715C]">最大200文字</p>
                    </CardContent>
                </Card>

                <Button
                    type="button"
                    className="h-12 rounded-full bg-[#6B4F3A] text-white hover:bg-[#5A4230]"
                    disabled
                >
                    <Plus className="mr-2 h-4 w-4" aria-hidden="true" />
                    登録する
                </Button>
            </div>
        </main>
    );
}