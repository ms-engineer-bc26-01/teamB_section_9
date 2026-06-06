"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api/fetcher";

type HealthResponse = {
  status: string;
  service: string;
};

export default function ApiCallSamplePage() {
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(true);

  const loadHealth = async () => {
    setIsLoadingHealth(true);
    setHealthError(null);

    try {
      const response = await apiFetch<HealthResponse>("/health");
      console.log("GET /api/v1/health success", response);
      setHealthData(response);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unknown error occurred";
      console.error("GET /api/v1/health failed", error);
      setHealthData(null);
      setHealthError(message);
    } finally {
      setIsLoadingHealth(false);
    }
  };

  useEffect(() => {
    let isActive = true;

    const fetchInitialHealth = async () => {
      try {
        const response = await apiFetch<HealthResponse>("/health");
        console.log("GET /api/v1/health success", response);

        if (!isActive) {
          return;
        }

        setHealthData(response);
        setHealthError(null);
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Unknown error occurred";
        console.error("GET /api/v1/health failed", error);

        if (!isActive) {
          return;
        }

        setHealthData(null);
        setHealthError(message);
      } finally {
        if (isActive) {
          setIsLoadingHealth(false);
        }
      }
    };

    void fetchInitialHealth();

    return () => {
      isActive = false;
    };
  }, []);

  return (
    <main className="min-h-screen bg-[#FAF8F5] px-4 py-6 text-[#2B2926]">
      <div className="mx-auto max-w-[390px] space-y-6">
        <header className="space-y-1">
          <p className="text-sm text-[#8C715C]">Climo API Call Sample</p>
          <h1 className="text-2xl font-bold">API通信サンプル</h1>
          <p className="text-sm text-muted-foreground">
            fetcher 経由で backend API を呼ぶ確認ページです。
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>Backend Health Check</CardTitle>
            <CardDescription>
              GET /api/v1/health を呼び、結果を UI と console に出します。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2">
              <Button
                onClick={() => void loadHealth()}
                disabled={isLoadingHealth}
              >
                {isLoadingHealth ? "確認中..." : "health を再取得"}
              </Button>
              {healthData ? <Badge>success</Badge> : null}
              {healthError ? <Badge variant="destructive">error</Badge> : null}
            </div>

            <div className="rounded-2xl border bg-white p-4 text-sm shadow-sm">
              {isLoadingHealth ? (
                <p>バックエンドへリクエストしています...</p>
              ) : null}

              {!isLoadingHealth && healthData ? (
                <div className="space-y-1">
                  <p>通信成功</p>
                  <p>status: {healthData.status}</p>
                  <p>service: {healthData.service}</p>
                </div>
              ) : null}

              {!isLoadingHealth && healthError ? (
                <div className="space-y-1 text-red-600">
                  <p>通信失敗</p>
                  <p>{healthError}</p>
                </div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
