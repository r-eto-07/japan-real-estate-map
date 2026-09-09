import type { Area } from "../types/area";
import { Loading } from "./Loading";

interface AreaDetailPanelProps {
  area: Area | null;
  loading: boolean;
  error: string | null;
}

const numberFormatter = new Intl.NumberFormat("ja-JP");

function formatYen(value: number): string {
  return `${numberFormatter.format(value)}円`;
}

const LAND_PRICE_SOURCE = "国土交通省 不動産情報ライブラリ";
const RENT_NOTE = "住宅・土地統計調査による市区町村単位の借家平均家賃（2023年時点）";
const TRANSACTION_NOTE =
  "市区町村内の宅地(土地)取引の集計値。地価公示地点と実際の取引は位置・用途・条件が異なるため参考値です。";

export function AreaDetailPanel({ area, loading, error }: AreaDetailPanelProps) {
  return (
    <aside className="detail-panel">
      <h2 className="detail-panel__title">地域詳細</h2>
      {renderBody({ area, loading, error })}
    </aside>
  );
}

function renderBody({ area, loading, error }: AreaDetailPanelProps) {
  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <p className="detail-panel__message detail-panel__message--error">{error}</p>
    );
  }

  if (!area) {
    return (
      <p className="detail-panel__message">地図から地域を選択してください。</p>
    );
  }

  return (
    <div className="area-detail">
      <p className="area-detail__place">
        {area.prefecture} {area.city}
      </p>

      {renderRent(area)}
      {renderLandPrice(area)}
      {renderTransaction(area)}
    </div>
  );
}

function renderRent(area: Area) {
  return (
    <section className="area-detail__section">
      <h3 className="area-detail__heading">家賃</h3>
      <dl className="area-detail__list">
        <div className="area-detail__row">
          <dt>平均家賃</dt>
          <dd className={area.averageRent === null ? "area-detail__muted" : undefined}>
            {area.averageRent !== null
              ? `${formatYen(area.averageRent)}/月`
              : "データなし"}
          </dd>
        </div>
        <div className="area-detail__row">
          <dt>調査年</dt>
          <dd>{area.rentYear !== null ? `${area.rentYear}年` : "－"}</dd>
        </div>
      </dl>
      {area.rentSource !== null && (
        <p className="area-detail__source">出典: {area.rentSource}</p>
      )}
      <p className="area-detail__note">{RENT_NOTE}</p>
    </section>
  );
}

function renderLandPrice(area: Area) {
  const { landPricePerSqm, landPrice100sqm, landPriceYear, landPriceSampleCount } =
    area;

  return (
    <section className="area-detail__section">
      <h3 className="area-detail__heading">公的地価（地価公示）</h3>
      {landPricePerSqm === null ? (
        <dl className="area-detail__list">
          <div className="area-detail__row">
            <dt>周辺地価公示中央値</dt>
            <dd className="area-detail__muted">
              周辺の地価公示データがありません
            </dd>
          </div>
        </dl>
      ) : (
        <dl className="area-detail__list">
          <div className="area-detail__row">
            <dt>周辺地価公示中央値</dt>
            <dd>{formatYen(landPricePerSqm)}/㎡</dd>
          </div>
          <div className="area-detail__row">
            <dt>100㎡換算</dt>
            <dd>
              {landPrice100sqm !== null ? formatYen(landPrice100sqm) : "データなし"}
            </dd>
          </div>
          <div className="area-detail__row">
            <dt>地価公示</dt>
            <dd>
              {landPriceYear !== null ? `${landPriceYear}年` : "年不明"} /{" "}
              {landPriceSampleCount}地点
            </dd>
          </div>
        </dl>
      )}
      <p className="area-detail__source">出典: {LAND_PRICE_SOURCE}</p>
    </section>
  );
}

function renderTransaction(area: Area) {
  const {
    transactionLandPricePerSqm,
    transactionLandPrice100sqm,
    transactionSampleCount,
    transactionPriceYear,
    landPricePerSqm,
  } = area;

  return (
    <section className="area-detail__section">
      <h3 className="area-detail__heading">実取引（土地）</h3>
      {transactionLandPricePerSqm === null ? (
        <dl className="area-detail__list">
          <div className="area-detail__row">
            <dt>土地取引単価中央値</dt>
            <dd className="area-detail__muted">取引データなし</dd>
          </div>
        </dl>
      ) : (
        <dl className="area-detail__list">
          <div className="area-detail__row">
            <dt>土地取引単価中央値</dt>
            <dd>{formatYen(transactionLandPricePerSqm)}/㎡</dd>
          </div>
          <div className="area-detail__row">
            <dt>100㎡換算参考額</dt>
            <dd>
              {transactionLandPrice100sqm !== null
                ? formatYen(transactionLandPrice100sqm)
                : "データなし"}
            </dd>
          </div>
          <div className="area-detail__row">
            <dt>取引件数</dt>
            <dd>
              {transactionSampleCount}件
              {transactionPriceYear !== null ? ` / ${transactionPriceYear}年` : ""}
            </dd>
          </div>
          {landPricePerSqm !== null && (
            <div className="area-detail__row">
              <dt>公示地価比</dt>
              <dd>
                {Math.round(
                  (transactionLandPricePerSqm / landPricePerSqm) * 100,
                )}
                %
              </dd>
            </div>
          )}
        </dl>
      )}
      <p className="area-detail__source">出典: {LAND_PRICE_SOURCE}（不動産取引価格情報）</p>
      <p className="area-detail__note">{TRANSACTION_NOTE}</p>
    </section>
  );
}
