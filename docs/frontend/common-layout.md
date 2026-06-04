# 共通レイアウト設計書

## 概要

Climo フロントエンドにおける共通レイアウトを定義する。

本レイアウトは全画面で共通利用し、ユーザーがどの画面に遷移しても統一された操作体験を提供することを目的とする。

---

## 対象タスク

* S2-A-2-3 共通レイアウト作成

---

## 構成

### Header

表示内容

* アプリロゴ（Climo、将来追加予定）
* 画面タイトル（将来追加予定）

役割

* アプリ全体のブランド表示（将来追加予定）
* 上部ナビゲーション（将来追加予定）

---

### Main

各画面固有のコンテンツを表示する領域。

Next.js App Router の children を描画する。

---

### Bottom Navigation

モバイルでは画面下部、デスクトップでは画面右側に固定表示するナビゲーション。

表示項目

| メニュー    | 遷移先      |
| ------- | -------- |
| ホーム    | /        |
| 登録      | /clothes/new |
| お気に入り | /favorites |
| マイページ | /mypage  |

役割

* 主要機能への素早い遷移

---

### Footer

PC表示時のみ表示。

表示内容

* Copyright
* アプリ名

役割

* PC画面利用時の補足情報表示

---

## レスポンシブ方針

### Mobile

対象

* 〜768px

表示

* Header
* Main
* Bottom Navigation

Footer は非表示

---

### Desktop

対象

* 769px〜

表示

* Header
* Main
* Footer
* Bottom Navigation

Bottom Navigation は画面右側に縦配置で表示

---

## 実装ファイル

```text
src/
├── app/
│   └── layout.tsx
│
├── components/
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── BottomNavigation.tsx
```

---

## 使用技術

* Next.js App Router
* React
* Tailwind CSS
* shadcn/ui

---

## 今後の拡張予定

* 認証状態によるメニュー切り替え
* アクティブタブ表示
* 通知アイコン追加
* プロフィールアイコン追加
* ダークモード対応
