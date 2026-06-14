# Redis キャッシュ設計

天気予報など、外部 API への重複リクエストを抑制するためのキャッシュ方針をまとめる。
接続基盤は [`app/core/redis.py`](../app/core/redis.py) を参照。

## 目的

- Open-Meteo など外部 API への重複リクエストを TTL の間だけ抑制する。
- レスポンスの `cached` フィールドで、キャッシュ由来かどうかをクライアントに伝える。
- **Redis 障害時も API は劣化させない**（キャッシュミス扱いで処理を継続する）。

## キー命名規約

| 用途 | キー形式 | 例 |
|------|---------|----|
| 天気予報 | `weather:{latitude}:{longitude}:{days}` | `weather:35.6895:139.6917:3` |
| コーデ提案（将来） | `outfit:{user_id}:{...}` | （未実装・別タスク） |

- 天気は緯度経度と日数で結果が一意に定まるため、これらをキーにする。
  緯度経度は [`app/constants/regions.py`](../app/constants/regions.py) の固定値なのでキーは安定する。

## 値フォーマット

- JSON 文字列で保存する。クライアントは `decode_responses=True` のため、
  取得値は `str`。`json.dumps` / `json.loads` で相互変換する。

## TTL ポリシー

| 用途 | 設定値 | デフォルト |
|------|--------|-----------|
| 天気 | `settings.REDIS_WEATHER_TTL_SECONDS` | 1800 秒（30 分） |
| コーデ（将来） | `settings.REDIS_OUTFIT_TTL_SECONDS` | 86400 秒（24 時間） |

設定は [`app/core/config.py`](../app/core/config.py) を参照。

## `cached` フラグの挙動

- **キャッシュミス**: 外部 API を実際に呼び出す。レスポンスは `cached: false`。
  この結果をキャッシュに保存する（保存値も `cached: false` のまま）。
- **キャッシュヒット**: 外部 API を呼ばず、保存値を返す。返却直前に `cached: true` に上書きする。

## 障害時方針（graceful degradation）

- Redis への get/set で `RedisError` が発生した場合は **握りつぶす**。
  - get 失敗 → キャッシュミス扱い（`None` を返す）。
  - set 失敗 → 何もしない（API レスポンスには影響させない）。
- 失敗時は `WARNING` ログを 1 本出すのみ（ERROR にはしない＝復旧可能な劣化のため）。
- この方針は既存の `ping_redis()`（`RedisError` を握りつぶして `False` を返す）と一貫させる。

## 失効

- TTL による自動削除のみ。明示的な invalidation は現状不要。
- 検証は `redis-cli TTL <key>` で残 TTL を確認、`DEL <key>` または TTL 経過で
  再取得時に `cached: false` へ戻ることを確認する。
