# Climo デザインシステム

> 本ドキュメントは Climo のUI/UXデザインに関する正とする。  
> 要件は requirements.md、API仕様は openapi.yaml を参照する。

---

# 1. デザインコンセプト

## サービスコンセプト

> 朝の服選び、もう迷わない。

天気と手持ち服から、その日の最適なコーディネートを提案するAIスタイリスト。

---

## デザインキーワード

- Natural
- Minimal
- Calm
- Intelligent
- Timeless

---

## 目指す印象

- 忙しい朝でも迷わない
- 情報量は少なく見える
- 落ち着いている
- 女性向けだが甘すぎない
- AI感よりライフスタイル感

---

# 2. レイアウトルール

## 基本方針

スマホファーストで設計する。

---

## 基準幅

```txt
390px
```

対象端末

- iPhone 15
- iPhone 16
- Pixel系

---

## PC表示

PC表示時は中央にスマホ画面を配置する。

```txt
┌─────────────────────────┐
│                         │
│      390px UI領域       │
│                         │
└─────────────────────────┘
```

左右は余白または補助情報エリアとする。

---

## コンテンツ幅

```css
max-width: 390px;
margin: 0 auto;
```

---

# 3. カラールール

## ベースカラー

### Background

```css
#FAF8F5
```

または

```css
#FFFFFF
```

---

## テキストカラー

### Primary Text

```css
#2B2926
```

### Secondary Text

```css
#666666
```

---

## アクセントカラー

### Primary Accent

```css
#6B4F3A
```

### Secondary Accent

```css
#8C715C
```

---

## 状態カラー

### Success

```css
#16A34A
```

### Warning

```css
#F59E0B
```

### Error

```css
#DC2626
```
---
## デザイントークン

| Name | Value |
|--------|--------|
| color-background | #FAF8F5 |
| color-text-primary | #2B2926 |
| color-text-secondary | #666666 |
| color-accent-primary | #6B4F3A |
| color-accent-secondary | #8C715C |

---

# 4. タイポグラフィ

## フォント

優先順位

```txt
Figtree
↓
Geist
↓
sans-serif
```

日本語表示は現状のブラウザ標準フォールバックを使用する。

---

## 文字サイズ

### ページタイトル

```css
font-size: 24px;
font-weight: 700;
```

---

### セクションタイトル

```css
font-size: 18px;
font-weight: 600;
```

---

### 本文

```css
font-size: 14px〜16px;
```

---

### 補足テキスト

```css
font-size: 12px;
color: #666666;
```

---

# 5. コンポーネントルール

## UIライブラリ

```txt
shadcn/ui
```

を標準採用する。

---

## Card

基本UIはカードベースとする。
角丸は shadcn/ui 標準を基本とする

### ルール

- 余白を広く取る
- 影は最小限
- 境界線は薄くする
- 情報を詰め込みすぎない

### 推奨

```tsx
<Card>
  <CardHeader />
  <CardContent />
</Card>
```

---

## Button

### Primary Button

用途

- 登録
- 保存
- 提案生成
- ログイン

スタイル

```txt
背景：ブラウン
文字：白
```

標準ボタン高さ

- 40px〜44px

---

### Secondary Button

用途

- 戻る
- キャンセル
- スキップ

スタイル

```txt
背景：白
枠線あり
```

---

## Input

ルール

- ラベル必須
- プレースホルダーは補助説明扱い
- 必須入力は明示する

---

# 6. アイコンルール

## ライブラリ

```txt
lucide-react
```

現時点のフロントエンド実装では lucide-react を標準採用する。

components.json の設定変更を行う場合は、
本ドキュメントも合わせて更新すること。

---

## 使用方針

アイコンのみで意味を伝えない。

```txt
アイコン + テキスト
```

を基本とする。

---

## 装飾アイコン

装飾目的の場合は以下を付与する。

```tsx
aria-hidden="true"
```

---

# 7. 余白ルール

## 基本グリッド

```txt
4px
```

---

## 推奨スペーシング

```txt
4
8
12
16
24
32
```

---

## セクション間

```txt
24px
```

---

## カード内余白

```txt
16px
```

---

## ページ余白

```txt
左右16px
```

---

# 8. 画像ルール

## MVP方針

画像は補助情報とする。

主役はテキスト情報。

---

## 服画像

アスペクト比

```txt
1:1
```

---

## コーデ画像

将来的な画像表示時

```txt
4:5
```

推奨

---

## アップロード画像

推奨形式

```txt
jpg
png
webp
```

---

# 9. ナビゲーションルール

## メイン導線

```txt
ホーム
↓
シーン選択
↓
提案生成
↓
コーデ詳細
```

---

## 下部ナビゲーション

主要項目

```txt
ホーム
登録
お気に入り
マイページ
```

---

## 戻る導線

原則として各画面に戻る導線を配置する。

---

# 10. アクセシビリティ

## ランドマーク

アプリ全体の主要コンテンツ領域は layout.tsx で

```tsx
<main>
```

を使用する。

個別ページでは原則として <main> を重ねず、section または div を使用する。

---

## アイコン

装飾アイコンには

```tsx
aria-hidden="true"
```

を付与する。

---

## ボタン

文脈が伝わりにくい場合は

```tsx
aria-label
```

を付与する。

例

```tsx
<Button aria-label="オフィス向けコーデを見る">
```

---

## フォーム

- label を必須とする
- エラーメッセージを表示する
- キーボード操作可能とする

---

## コントラスト

WCAG AA準拠を目標とする。

---

## ローディングルール

ローディング中は
スピナー + 説明テキスト

例：
「おすすめコーデを考えています」

## Empty State

データ未登録時は
次の行動を促すCTAを表示する

例：
「服を登録する」

# 11. 実装ルール

## 技術構成

```txt
Next.js App Router
Tailwind CSS v4
shadcn/ui
lucide-react
```

現時点のフロントエンド実装では lucide-react を標準採用する。

components.json の設定変更を行う場合は、
本ドキュメントも合わせて更新すること。

---

## スタイリング方針

優先順位

```txt
Tailwind Utility
↓
shadcn/ui
↓
独自CSS
```

---

## コンポーネント設計

共通化できるものは

```txt
frontend/src/components/
```

へ配置する。

機能固有のものは

```txt
frontend/src/features/
```

へ配置する。

---

# 12. 今後追加予定

以下はMVP後に整理する。

- ダークモード
- アニメーションガイドライン
- グラフ表示ルール
- Empty Stateデザイン
- Skeletonデザイン
- Toastデザイン
- モーダルデザイン
- AI提案結果表示ルール
