"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
    ArrowLeft,
    CreditCard,
    LogOut,
    MapPin,
    Settings,
    Sparkles,
    UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { apiClient } from "@/lib/api/client";
import { supabase } from "@/lib/auth";
import { useAuthStore } from "@/stores/auth-store";

type UserProfile = {
    id: string;
    email: string;
    display_name: string | null;
    default_region_code: string | null;
    subscription_status: "free" | "active" | "canceled";
    stripe_customer_id: string | null;
    created_at: string;
};

type Region = {
    code: string;
    prefecture_code: string;
    prefecture_name: string;
    name: string;
    city: string;
    latitude: number;
    longitude: number;
};

type RegionsResponse = {
    items: Region[];
};

const SECONDARY_REGION_STORAGE_KEY = "climo.secondary_region_code";
const HOME_SCENE_STORAGE_KEY = "climo.home_scene_tpo";

const scenes = [
    { label: "オフィス", value: "business" },
    { label: "カジュアル", value: "casual" },
    { label: "フォーマル", value: "formal" },
    { label: "セレモニー", value: "ceremony" },
    { label: "レジャー", value: "leisure" },
];

function getPlanLabel(status: UserProfile["subscription_status"] | undefined) {
    switch (status) {
        case "active":
            return "プレミアム";
        case "canceled":
            return "解約済み";
        case "free":
        default:
            return "無料プラン";
    }
}

function getRegionLabel(region: Region) {
    return `${region.prefecture_name} ${region.name}`;
}

export default function SettingsPage() {
    const router = useRouter();
    const { session, user, clearAuth } = useAuthStore();

    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [regions, setRegions] = useState<Region[]>([]);
    const [primaryRegionCode, setPrimaryRegionCode] = useState("");
    const [secondaryRegionCode, setSecondaryRegionCode] = useState("");
    const [homeSceneTpo, setHomeSceneTpo] = useState("business");
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isLoggingOut, setIsLoggingOut] = useState(false);

    useEffect(() => {
        const token = session?.access_token;

        if (!token) {
            router.replace("/login");
            return;
        }

        let isMounted = true;

        async function fetchSettingsData() {
            try {
                const [me, regionResponse] = await Promise.all([
                    apiClient.get<UserProfile>("/auth/me", { token }),
                    apiClient.get<RegionsResponse>("/regions"),
                ]);

                if (!isMounted) return;

                const savedSecondaryRegionCode =
                    window.localStorage.getItem(SECONDARY_REGION_STORAGE_KEY) ?? "";
                const savedHomeSceneTpo =
                    window.localStorage.getItem(HOME_SCENE_STORAGE_KEY) ?? "business";

                setProfile(me);
                setRegions(regionResponse.items);
                setPrimaryRegionCode(me.default_region_code ?? "");
                setSecondaryRegionCode(savedSecondaryRegionCode);
                setHomeSceneTpo(savedHomeSceneTpo);
            } catch {
                if (!isMounted) return;
                setErrorMessage("設定情報を取得できませんでした。時間をおいて再度お試しください。");
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }

        fetchSettingsData();

        return () => {
            isMounted = false;
        };
    }, [router, session?.access_token]);

    const displayName = useMemo(() => {
        const metadataName = user?.user_metadata?.display_name;
        if (typeof metadataName === "string" && metadataName.trim().length > 0) {
            return metadataName.trim();
        }

        return profile?.display_name ?? "ユーザー";
    }, [profile?.display_name, user?.user_metadata]);

    const email = profile?.email ?? user?.email ?? "";
    const planLabel = getPlanLabel(profile?.subscription_status);

    const handleSave = async () => {
        const token = session?.access_token;

        if (!token) {
            setErrorMessage("ログイン情報を確認できませんでした。再度ログインしてください。");
            return;
        }

        if (!primaryRegionCode || !secondaryRegionCode) {
            setErrorMessage("地域1と地域2を選択してください。");
            setSuccessMessage(null);
            return;
        }

        setIsSaving(true);
        setErrorMessage(null);
        setSuccessMessage(null);

        try {
            const updatedProfile = await apiClient.put<UserProfile>(
                "/auth/me/default-region",
                { region_code: primaryRegionCode },
                { token },
            );

            window.localStorage.setItem(
                SECONDARY_REGION_STORAGE_KEY,
                secondaryRegionCode,
            );
            window.localStorage.setItem(HOME_SCENE_STORAGE_KEY, homeSceneTpo);

            setProfile(updatedProfile);
            setSuccessMessage("設定を保存しました。");
        } catch {
            setErrorMessage("設定を保存できませんでした。入力内容を確認してください。");
        } finally {
            setIsSaving(false);
        }
    };

    const handleLogout = async () => {
        setIsLoggingOut(true);
        setErrorMessage(null);
        setSuccessMessage(null);

        try {
            await supabase.auth.signOut();
            clearAuth();
            router.replace("/login");
        } catch {
            setErrorMessage("ログアウトできませんでした。時間をおいて再度お試しください。");
            setIsLoggingOut(false);
        }
    };

    return (
        <div className="space-y-5">
            <section aria-labelledby="settings-heading" className="space-y-3">
                <Button
                    asChild
                    variant="ghost"
                    className="h-9 px-0 text-[#6B4F3A] hover:bg-transparent"
                >
                    <Link href="/mypage">
                        <ArrowLeft aria-hidden="true" size={18} />
                        マイページへ戻る
                    </Link>
                </Button>

                <div className="flex items-start justify-between gap-4">
                    <div>
                        <p className="text-sm font-medium text-[#8C715C]">Settings</p>
                        <h1
                            id="settings-heading"
                            className="mt-1 text-2xl font-bold leading-tight text-[#2B2926]"
                        >
                            設定
                        </h1>
                        <p className="mt-1 text-sm leading-6 text-[#6F6258]">
                            アカウントとコーデ提案の基本設定を管理します。
                        </p>
                    </div>

                    <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#EAF4F0] text-[#2F6F63]">
                        <Settings aria-hidden="true" size={25} />
                    </div>
                </div>
            </section>

            {errorMessage ? (
                <div
                    role="alert"
                    className="rounded-lg border border-[#E8DED4] bg-white px-4 py-3 text-sm text-[#8C3D2F]"
                >
                    {errorMessage}
                </div>
            ) : null}

            {successMessage ? (
                <div
                    role="status"
                    className="rounded-lg border border-[#D6E7DD] bg-[#F6FAF8] px-4 py-3 text-sm text-[#2F6F63]"
                >
                    {successMessage}
                </div>
            ) : null}

            <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <UserRound aria-hidden="true" size={18} className="text-[#6B4F3A]" />
                        アカウント状態
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                    <div>
                        <p className="text-xs font-medium text-[#8C715C]">表示名</p>
                        <p className="mt-1 font-semibold text-[#2B2926]">
                            {isLoading ? "-" : displayName}
                        </p>
                    </div>

                    <div>
                        <p className="text-xs font-medium text-[#8C715C]">メールアドレス</p>
                        <p className="mt-1 break-all font-semibold text-[#2B2926]">
                            {isLoading ? "-" : email}
                        </p>
                    </div>

                    <div>
                        <p className="text-xs font-medium text-[#8C715C]">プラン</p>
                        <p className="mt-1 font-semibold text-[#2B2926]">
                            {isLoading ? "-" : planLabel}
                        </p>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <MapPin aria-hidden="true" size={18} className="text-[#6B4F3A]" />
                        地域設定
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <label
                            htmlFor="primary-region"
                            className="text-sm font-medium text-[#4B3A2F]"
                        >
                            地域1
                        </label>
                        <Select
                            value={primaryRegionCode}
                            onValueChange={setPrimaryRegionCode}
                            disabled={isLoading || regions.length === 0}
                        >
                            <SelectTrigger id="primary-region" className="h-11 w-full">
                                <SelectValue placeholder="地域1を選択" />
                            </SelectTrigger>
                            <SelectContent>
                                {regions.map((region) => (
                                    <SelectItem key={region.code} value={region.code}>
                                        {getRegionLabel(region)}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <p className="text-xs leading-5 text-[#8C715C]">
                            コーデ提案の天気取得に使うメイン地域です。
                        </p>
                    </div>

                    <div className="space-y-2">
                        <label
                            htmlFor="secondary-region"
                            className="text-sm font-medium text-[#4B3A2F]"
                        >
                            地域2
                        </label>
                        <Select
                            value={secondaryRegionCode}
                            onValueChange={setSecondaryRegionCode}
                            disabled={isLoading || regions.length === 0}
                        >
                            <SelectTrigger id="secondary-region" className="h-11 w-full">
                                <SelectValue placeholder="地域2を選択" />
                            </SelectTrigger>
                            <SelectContent>
                                {regions.map((region) => (
                                    <SelectItem key={region.code} value={region.code}>
                                        {getRegionLabel(region)}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <p className="text-xs leading-5 text-[#8C715C]">
                            通勤先やよく行く場所など、比較用の地域として保存します。
                        </p>
                    </div>
                </CardContent>
            </Card>

            <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <Sparkles aria-hidden="true" size={18} className="text-[#C0784A]" />
                        トップページのシーン
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                    <label
                        htmlFor="home-scene"
                        className="text-sm font-medium text-[#4B3A2F]"
                    >
                        コーデのシーン
                    </label>
                    <Select value={homeSceneTpo} onValueChange={setHomeSceneTpo}>
                        <SelectTrigger id="home-scene" className="h-11 w-full">
                            <SelectValue placeholder="シーンを選択" />
                        </SelectTrigger>
                        <SelectContent>
                            {scenes.map((scene) => (
                                <SelectItem key={scene.value} value={scene.value}>
                                    {scene.label}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                    <p className="text-xs leading-5 text-[#8C715C]">
                        トップページで最初に表示するおすすめコーデのシーンです。
                    </p>
                </CardContent>
            </Card>

            <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                        <CreditCard aria-hidden="true" size={18} className="text-[#6B4F3A]" />
                        プラン
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    <p className="text-sm text-[#6F6258]">
                        現在のプランは
                        <span className="font-bold text-[#2B2926]"> {planLabel} </span>
                        です。
                    </p>
                    <Button
                        type="button"
                        variant="outline"
                        className="h-11 w-full rounded-lg border-[#E8DED4]"
                        disabled
                    >
                        プラン管理は準備中です
                    </Button>
                </CardContent>
            </Card>

            <div className="space-y-3">
                <Button
                    type="button"
                    className="h-12 w-full rounded-lg bg-[#2F6F63] text-base font-bold text-white hover:bg-[#285F55]"
                    disabled={isLoading || isSaving}
                    onClick={handleSave}
                >
                    {isSaving ? "保存中..." : "設定を保存する"}
                </Button>

                <Button
                    type="button"
                    variant="outline"
                    className="h-12 w-full rounded-lg border-[#E8DED4] text-base font-bold text-[#8C3D2F]"
                    disabled={isLoggingOut}
                    onClick={handleLogout}
                >
                    <LogOut aria-hidden="true" size={18} />
                    {isLoggingOut ? "ログアウト中..." : "ログアウト"}
                </Button>
            </div>
        </div>
    );
}