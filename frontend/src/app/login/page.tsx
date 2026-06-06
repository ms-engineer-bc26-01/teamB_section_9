import Link from "next/link";
import { LogIn } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function LoginPage() {
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
                                placeholder="example@email.com"
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
                                placeholder="********"
                            />
                        </div>

                        <Button className="w-full bg-[#6B4F3A] hover:bg-[#5A412F]">
                            ログイン
                        </Button>

                        <div className="text-center text-sm text-muted-foreground">
                            アカウントをお持ちでない方
                        </div>

                        <Button asChild variant="outline" className="w-full">
                            <Link href="/register">
                                新規登録はこちら
                            </Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}