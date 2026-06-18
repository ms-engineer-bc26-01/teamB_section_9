"use client";

import Link from "next/link";
// import { useRouter } from "next/navigation"; メール確認ON/OFF時の挙動をまだ確定していないため、ルーターは一旦保留とする
import { FormEvent, useState } from "react";

import { supabase } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function RegisterPage() {
    // const router = useRouter();

    const [displayName, setDisplayName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [passwordConfirm, setPasswordConfirm] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();

        setErrorMessage("");
        setSuccessMessage("");

        if (!email || !password || !passwordConfirm) {
            setErrorMessage("メールアドレスとパスワードを入力してください。");
            return;
        }

        if (password.length < 8) {
            setErrorMessage("パスワードは8文字以上で入力してください。");
            return;
        }

        if (password !== passwordConfirm) {
            setErrorMessage("確認用パスワードが一致しません。");
            return;
        }

        setIsSubmitting(true);

        try {
            const { error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        display_name: displayName,
                    },
                },
            });

            if (error) {
                setErrorMessage(
                    "アカウント登録に失敗しました。入力内容を確認してください。",
                );
                return;
            }

            setSuccessMessage(
                "確認メールを送信しました。メール内のリンクを確認してください。",
            );
        } catch {
            setErrorMessage(
                "通信エラーが発生しました。時間をおいて再度お試しください。",
            );
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#FAF8F5] px-5 py-10 text-[#222222]">
            <div className="mx-auto flex min-h-[calc(100vh-5rem)] w-full max-w-[390px] items-center">
                <Card className="w-full border-[#E8DED4] bg-white shadow-sm">
                    <CardHeader className="space-y-2">
                        <p className="text-sm font-medium text-[#8C715C]">Climo</p>
                        <CardTitle className="text-2xl">アカウント登録</CardTitle>
                        <CardDescription>
                            メールアドレスとパスワードを登録して、今日のコーデ提案を始めましょう。
                        </CardDescription>
                    </CardHeader>

                    <CardContent>
                        <form className="space-y-5" onSubmit={handleSubmit}>
                            <div className="space-y-2">
                                <label htmlFor="display-name">表示名</label>
                                <Input
                                    id="display-name"
                                    name="displayName"
                                    type="text"
                                    autoComplete="name"
                                    placeholder="例：Yui"
                                    value={displayName}
                                    onChange={(event) => setDisplayName(event.target.value)}
                                />
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="email" className="text-sm font-medium">
                                    メールアドレス
                                </label>
                                <Input
                                    id="email"
                                    name="email"
                                    type="email"
                                    autoComplete="email"
                                    placeholder="example@example.com"
                                    value={email}
                                    onChange={(event) => setEmail(event.target.value)}
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="password">パスワード</label>
                                <Input
                                    id="password"
                                    name="password"
                                    type="password"
                                    autoComplete="new-password"
                                    placeholder="8文字以上"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="password-confirm">パスワード確認</label>
                                <Input
                                    id="password-confirm"
                                    name="passwordConfirm"
                                    type="password"
                                    autoComplete="new-password"
                                    placeholder="もう一度入力"
                                    value={passwordConfirm}
                                    onChange={(event) => setPasswordConfirm(event.target.value)}
                                    required
                                />
                            </div>

                            {errorMessage && (
                                <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                                    {errorMessage}
                                </p>
                            )}

                            {successMessage && (
                                <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
                                    {successMessage}
                                </p>
                            )}

                            <Button
                                type="submit"
                                className="w-full bg-[#6B4F3A] text-white hover:bg-[#5A422F]"
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? "登録中..." : "登録する"}
                            </Button>

                            <p className="text-xs leading-5 text-[#8C715C]">
                                登録することで、
                                <Link
                                    href="/terms"
                                    className="font-medium underline-offset-4 hover:underline"
                                >
                                    利用規約
                                </Link>
                                および
                                <Link
                                    href="/privacy"
                                    className="font-medium underline-offset-4 hover:underline"
                                >
                                    プライバシーポリシー
                                </Link>
                                に同意したものとみなします。
                            </p>
                        </form>

                        <p className="mt-6 text-center text-sm text-[#666666]">
                            すでにアカウントをお持ちですか？{" "}
                            <Link
                                href="/login"
                                className="font-medium text-[#6B4F3A] underline-offset-4 hover:underline"
                            >
                                ログイン
                            </Link>
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
