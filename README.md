# 不動産エリア分析アプリ (Phase 5)

日本地図上の市区町村をクリックすると、その地域の

- 都道府県 / 市区町村名
- **平均家賃**（e-Stat 令和5年住宅・土地統計調査。無い地域は「データなし」）
- **周辺の地価公示中央値**（円 / ㎡） … 国土交通省「不動産情報ライブラリ」XPT002 の実データ
- **実取引の土地単価中央値**（円 / ㎡） … 同 XIT001（不動産取引価格情報）の実データ
- 100㎡換算参考額 / 各データの年・件数 / 公示地価比

を表示する Web アプリです。地図の行政区域は国土数値情報 行政区域データ (N03) 2026 年版の
実際の境界を使用しています（全国 1,900 弱の市区町村）。

**Phase 5**: 外部 API から取得したデータは **PostgreSQL に永続化**され、通常の画面操作は
PostgreSQL を参照します（`React → FastAPI → PostgreSQL → 画面`）。DB に無いデータだけ
外部 API を呼んで取得・保存する **cache-aside** 方式です。API レスポンス形式は Phase 4 と同一で、
Frontend は「データが DB か API か」を意識しません。

```text
外部データソース                アプリケーション
  e-Stat ┐                         React
  XPT002 ├─▶ 取得(sync/初回) ─▶ PostgreSQL ─▶ FastAPI ─▶ React
  XIT001 ┘                    （アプリ用データストア）

外部 API = 生データの取得元 /  PostgreSQL = アプリケーション用データストア
```

## データの定義と出典

| 項目 | 由来 |
| --- | --- |
| 行政区域ポリゴン | 国土交通省 国土数値情報 行政区域データ (N03)　データ基準日 2026-01-01。表示用に geometry 簡略化（tolerance 0.003 度・座標 4 桁）。 |
| 都道府県 / 市区町村名 (`municipalities.json`) | 同上（N03 由来）。GeoJSON と同一スクリプトで生成し Frontend / Backend の市区町村コードが一致。 |
| **平均家賃 (`averageRent`)** | **e-Stat「令和5年住宅・土地統計調査」表番号 112-3-2（統計表 ID `0004021480`）**。「住宅の種類=総数・家賃0円を含まない」の市区町村別平均家賃。**調査年 2023 年**。 |
| 公的地価 (`landPricePerSqm`) | 国土交通省「不動産情報ライブラリ」地価公示データ（**XPT002** API）。「市区町村全体の平均」ではなく、クリック地点周辺タイル内の同一市区町村の地価公示地点の**中央値**（外れ値対策）。 |
| **実取引土地単価 (`transactionLandPricePerSqm`)** | 国土交通省「不動産情報ライブラリ」**XIT001**（不動産取引価格情報）。対象は **`宅地(土地)`** のみ（`宅地(土地と建物)`・中古マンション等・農地・林地は集計しない）。`priceClassification=01`。指標は **市区町村内の㎡単価中央値**。対象年 **2025 年**（`config.TRANSACTION_PRICE_YEAR` で変更可）。 |
| 100㎡換算参考額 | 各㎡単価 × 100。参考値。 |

> **平均家賃の意味（重要）**
> これは「現在募集中の賃貸物件の募集賃料」ではありません。住宅・土地統計調査による
> **実際に借家に居住している世帯の家賃統計**で、**2023 年時点**の市区町村単位の借家平均家賃です。
> 「2026 年現在の家賃」ではない点に注意してください（画面にも「2023年時点」と明記）。
>
> **カバー範囲**: 住宅・土地統計調査は全ての町村について市区町村別結果が提供されるわけではありません。
> `municipalityCode` は存在するが e-Stat 家賃データが無い、は正常です（`averageRent: null` / 画面「データなし」）。データなしはバグではありません。

> **実取引土地単価の意味（重要）**
> `transactionLandPricePerSqm` は **市区町村単位の集計値**で、クリック位置そのものの土地価格を示すものではありません。
> また「公示地価比 = 実取引 / 地価公示」は参考表示です。地価公示地点と実際の取引物件は
> 位置・用途・道路条件・面積・形状が異なるため、100% 未満＝割安 / 以上＝割高 とは判断できません。
> 対象年に土地取引が無い市区町村では `transactionSampleCount: 0` / 画面「取引データなし」（404 ではない）。
>
> 出典表記（国土数値情報 利用規約に基づく）:「この地図は、国土交通省 国土数値情報（行政区域データ）を加工して作成したものです。」

---

## 技術スタック

| 層 | 使用技術 |
| --- | --- |
| Frontend | React + TypeScript + Vite + MapLibre GL JS |
| Backend | Python + FastAPI + Pydantic + httpx |
| DB | PostgreSQL 17（Docker）+ SQLAlchemy 2.x + Alembic + psycopg |
| データ生成 | Python + geopandas / shapely（`scripts/`） |

---

## ディレクトリ構成

```text
japan_map/
├─ docker-compose.yml              PostgreSQL 17（volume: postgres_data で永続化）
├─ scripts/
│  ├─ prepare_municipalities.py    N03 -> municipalities.geojson / municipalities.json
│  ├─ import_municipalities.py     municipalities.json -> PostgreSQL（UPSERT・再実行可）
│  ├─ sync_rent_statistics.py      e-Stat -> rent_statistics（UPSERT）
│  ├─ inspect_estat_meta.py        e-Stat 統計表のメタ情報を確認
│  └─ requirements.txt
└─ backend/
   ├─ alembic/ + alembic.ini       マイグレーション（4 テーブル）
   └─ app/
      ├─ config.py                 .env / 定数（DATABASE_URL・統計表 ID・対象年もここだけ）
      ├─ dependencies.py           get_db / get_area_service
      ├─ routers/area.py + meta.py HTTP 入出力のみ（SQL は書かない）。/api/health
      ├─ db/
      │  ├─ base.py / session.py   Engine / Session / get_db
      │  └─ models/                municipality / rent_statistic / land_price_point / transaction
      ├─ repositories/             municipality / rent / land_price / transaction（DB アクセスはここだけ）
      ├─ services/
      │  ├─ area_service.py        Repository 統合 + 中央値 + 100㎡換算。3 ソース独立
      │  ├─ rent_service.py        DB 優先・ミス時 e-Stat -> DB 保存
      │  ├─ land_price_service.py  DB 優先・ミス時 XPT002 -> DB 保存
      │  └─ transaction_service.py DB 優先・ミス時 XIT001 -> DB 保存
      ├─ clients/                  reinfolib_client（XPT002 / XIT001）/ estat_client（HTTP のみ）
      ├─ parsers/                  estat_rent_parser / land_price_parser
      ├─ utils/                    estat_area_code / transaction_parser / tile / price_parser
      └─ data/municipalities.json  ★prepare_municipalities.py の生成物（手編集しない）
```

責務分離（Phase 5）:

```text
JapanMap ─▶ areaApi ─▶ router ─▶ AreaService ─┬▶ MunicipalityRepository ─▶ PostgreSQL
                                              ├▶ RentService        ─┬▶ RentRepository ─▶ PostgreSQL
                                              ├▶ LandPriceService   ─┼▶ (DB ミス時) 外部 API ─▶ DB 保存
                                              └▶ TransactionService ─┘
```

- **通常の画面操作は PostgreSQL のみ**を参照する（DB にデータがあれば外部 API を呼ばない）。
- **DB ミス時だけ** 外部 API（e-Stat / XPT002 / XIT001）を呼び、結果を正規化して DB へ保存してから返す。
  生 JSON は保存せず、必要な項目のみカラムに正規化する。中央値・100㎡換算・公示地価比などの
  表示用計算は DB に保存せず AreaService で都度算出する。
- 地価公示は「中央値」ではなく **地点そのもの**（価格・座標・用途）を `land_price_points` に保存する。
- **3 つの外部データソースは独立**。どれか 1 つが落ちても他は返し、該当項目のみ `null` / `sampleCount: 0`。
  画面全体を 500 にしない。XIT001 の `HTTP 404` は「対象条件のデータなし」であり障害と区別する。
- Router は SQL を書かない。DB アクセスは `repositories/` に閉じ込める。
- コード変換・文字列解析はそれぞれ `utils/` `parsers/` に分離。
- e-Stat の分類コードは推測で固定せず、レスポンスのメタ情報（CLASS_INF）の**名称**から解決する
  （`config.ESTAT_RENT_HOUSING_TYPE_MATCH="総数"` / `ESTAT_RENT_AVERAGE_MATCH="含まない"`）。
  実際の名称・コードは `scripts/inspect_estat_meta.py` で確認できる。

---

## セットアップ

### 1. 全国市区町村データの生成（初回のみ）

```bash
backend\.venv\Scripts\python.exe -m pip install -r scripts/requirements.txt
backend\.venv\Scripts\python.exe scripts/prepare_municipalities.py
```

### 2. .env 設定（Backend）

`backend/.env.example` をコピーして `backend/.env` を作成します。

```bat
copy .env.example .env
```

| 変数 | 用途 | 取得先 / 値 |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL 接続 | `postgresql+psycopg://USER:PASSWORD@localhost:5432/DB`（`docker-compose.yml` の設定に合わせる） |
| `REINFOLIB_API_KEY` | 地価公示 XPT002 / 実取引 XIT001 | <https://www.reinfolib.mlit.go.jp/> |
| `ESTAT_APP_ID` | 平均家賃（e-Stat）※Reinfolib とは別物 | <https://www.e-stat.go.jp/api/>（無料登録） |

- API キーが未設定でも起動は可能。DB に無いデータを取得しようとしたときだけ該当項目が `null` になります。
- `.env` / パスワード / API キーはソース・README・ログに出しません（Git 管理対象外）。

### 3. PostgreSQL 起動 + マイグレーション + 初期データ投入

```bash
docker compose up -d            # PostgreSQL 17 を起動
docker compose ps               # STATUS が Up であること

cd backend
.venv\Scripts\python.exe -m alembic upgrade head        # 4 テーブル作成
.venv\Scripts\python.exe ../scripts/import_municipalities.py   # 市区町村マスタ投入（1,898 件）
.venv\Scripts\python.exe ../scripts/sync_rent_statistics.py    # 家賃を e-Stat から一括取得 -> DB（任意・要 ESTAT_APP_ID）
```

- 地価公示・実取引は初回クリック時に自動で取得・保存されます（`sync_*` は不要）。
  家賃も同様ですが、`sync_rent_statistics.py` を流しておくと以後 e-Stat を一切呼ばずに済みます。
- `ESTAT_APP_ID` 設定後、分類コードの確認は `python ../scripts/inspect_estat_meta.py`。

### 4. Backend / Frontend 起動

```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload      # → :8000

cd frontend
npm install
npm run dev                                                    # → :5173
```

DB 疎通は `GET http://localhost:8000/api/health` → `{"status":"ok","database":"connected"}`。

`.venv\Scripts\activate` が実行ポリシーで失敗する場合は
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` を一度実行するか、
上記のように `.venv\Scripts\python.exe` を直接呼んでください。

---

## API

### `GET /api/areas/{municipality_code}?lat={lat}&lon={lon}`

```json
{
  "municipalityCode": "12217",
  "prefecture": "千葉県",
  "city": "柏市",
  "averageRent": 68200,
  "rentYear": 2023,
  "rentSource": "e-Stat 令和5年住宅・土地統計調査",
  "landPricePerSqm": 165000,
  "landPrice100sqm": 16500000,
  "landPriceSource": "国土交通省 地価公示",
  "landPriceYear": 2026,
  "landPriceSampleCount": 4,
  "transactionLandPricePerSqm": 178000,
  "transactionLandPrice100sqm": 17800000,
  "transactionSampleCount": 42,
  "transactionPriceYear": 2025,
  "transactionPriceSource": "国土交通省 不動産取引価格情報"
}
```

- **404 は `municipalities.json`（N03 の正式な市区町村コード）に無いコードのときだけ。**
  家賃・地価公示・実取引のいずれかがデータなしでも 404 にしない
  （`averageRent: null` / `landPriceSampleCount: 0` / `transactionSampleCount: 0`）。
- **e-Stat / XPT002 / XIT001 は独立**。1 つが落ちても他は返る（`Promise.all` 的な全失敗にしない）。
  外部 API 由来の失敗で 5xx にはしない。
- 各 API の失敗（400/401/403/429/5xx/timeout）は Backend ログに記録（appId / API キーの値は出さない）。

政令指定都市は行政区単位（`14103` 横浜市西区）、東京 23 区は区単位（`13104` 新宿区）でコード取得できます。

---

## テスト

Backend (pytest):

```bash
cd backend
.venv\Scripts\python.exe -m pytest
```

- `test_price_parser.py` / `test_tile.py` … 地価: 円/㎡パース・タイル変換
- `test_reinfolib_client.py` … 国交省 XPT002（200/401/429/500/timeout。**本物の API は呼ばずモック**）
- `test_estat_rent_parser.py` … 家賃抽出（総数・含まない・対象自治体）と数値変換（`""` / `"-"` / `None` → `None`）
- `test_estat_client.py` … e-Stat（200 / STATUS 403 / 429 / 500 / timeout。**モック**）
- `test_estat_area_code.py` … 地域コード変換
- `test_transaction_parser.py` … `UnitPrice` 数値化 / `TradePrice`÷`Area` フォールバック / `Period` 解析 / ≤ 0 除外
- `test_land_price_parser.py` … XPT002 GeoJSON -> 対象自治体の地点（価格・座標・用途）
- `test_transaction_service.py` … `宅地(土地)` のみ中央値・件数 / 外れ値に強い中央値 / DB ミス時 XIT001 -> DB 保存
- `test_repositories.py` … Municipality/Rent/LandPrice/Transaction 各 Repository（自治体・年・種別での絞り込み・UPSERT）
- `test_area_api.py` … **DB 投入済みなら Area API が全項目を返す** / 未知コード 404 /
  **DB が揃っていれば外部 API を一切呼ばない** / **DB ミス時のみ外部 API -> DB 保存** /
  1 ソースが落ちても他は返る / `/api/health`
- `test_municipalities_data.py` … 生成 GeoJSON / JSON の検証

pytest は `DATABASE_URL` の DB 名に `_test` を付けた**別データベース**を自動作成して使うため、
開発用 DB を破壊しません。

```bash
.venv\Scripts\python.exe -m pytest ../scripts/     # 生成スクリプトの純粋関数
```

Frontend:

```bash
cd frontend
npm test        # AreaDetailPanel: 68,200円/月・調査年・出典 / averageRent=null → 「データなし」
npm run build
```

---

## データの永続化

PostgreSQL のデータは Docker volume `postgres_data` に保存されます。

- `docker compose down` … コンテナ停止。**データは volume に残る**。
- `docker compose down -v` … volume ごと削除。**データは消える**（再度マイグレーション + 投入が必要）。

再取得したい場合は該当テーブルを空にすれば、次回クリック時に外部 API から取得し直します。

---

## 今回（Phase 5）実装していない機能

PostGIS / Redis / Celery / Kafka / クラウド DB / Kubernetes / ユーザー認証 /
物件登録 / 投資スコア。DB 中心のデータ経路への移行に集中。全国データの事前一括ダウンロード
（地価公示・実取引）も未実装（クリック時 cache-aside のみ）。

### 今後の拡張予定

- 全国データの事前一括取得（地価公示・実取引）
- 路線価 / 人口 / 世帯数 / 空室率
- 物件入力 → 地域平均との比較（投資スクリーニング）
- 中央値の `percentile_cont`（PostgreSQL 側）化 / 1km 圏の地点検索（PostGIS）
