import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  // 開発サーバのリソース（JS チャンク / HMR / フォント）への別オリジンアクセスは
  // Next.js 16 では既定でブロックされる。スマホ実機を同一 LAN の private IP:3000 で
  // 開くと別オリジン扱いになりクライアント JS が配信されず、ハイドレーションが
  // 起きない（「認証状態を確認中…」で固まる）。同一 LAN の private 帯を許可して
  // 各自が自分の PC の LAN IP でスマホ実機検証できるようにする。dev 専用設定で
  // 本番ビルド/配信には影響しない。
  allowedDevOrigins: ["192.168.*.*", "10.*.*.*", "172.16.*.*", "172.31.*.*"],
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.supabase.co",
        pathname: "/storage/v1/object/**",
      },
    ],
  },
};

export default nextConfig;
