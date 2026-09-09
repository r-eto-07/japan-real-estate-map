/** Backend `/api/areas/{code}` のレスポンス型。 */
export interface Area {
  municipalityCode: string;
  prefecture: string;
  city: string;

  /** e-Stat 令和5年住宅・土地統計調査（2023 年・市区町村単位の借家平均家賃）。無ければ null */
  averageRent: number | null;
  rentYear: number | null;
  rentSource: string | null;

  /** クリック地点周辺タイル内・同一市区町村の地価公示地点の中央値（円/㎡） */
  landPricePerSqm: number | null;
  landPrice100sqm: number | null;

  landPriceSource: string | null;
  landPriceYear: number | null;
  landPriceSampleCount: number;

  /** 市区町村内の宅地(土地)取引の㎡単価中央値（国土交通省 XIT001）。無ければ null */
  transactionLandPricePerSqm: number | null;
  transactionLandPrice100sqm: number | null;
  transactionSampleCount: number;
  transactionPriceYear: number | null;
  transactionPriceSource: string | null;
}

/** 地図 GeoJSON の各 Feature が持つ properties。 */
export interface MunicipalityProperties {
  prefectureCode: string;
  municipalityCode: string;
  prefectureName: string;
  municipalityName: string;
}
