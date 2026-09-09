import type { Area } from "../types/area";

const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/** 市区町村コードが backend に登録されていない場合に投げる。 */
export class AreaNotFoundError extends Error {
  constructor(municipalityCode: string) {
    super(`Area not found: ${municipalityCode}`);
    this.name = "AreaNotFoundError";
  }
}

/**
 * 指定した市区町村コード + クリック地点の緯度経度でエリア情報を取得する。
 * React コンポーネントから fetch を直接呼ばず、必ずこの関数を経由する。
 * 外部 API（国交省 地価公示 / e-Stat 家賃）は backend 経由でのみ呼ぶ。
 * 個々の外部 API の失敗は backend 側で null 化されるため、ここで失敗するのは
 * 未知コード(404) か想定外のサーバエラーのみ。
 */
export async function getArea(
  municipalityCode: string,
  latitude: number,
  longitude: number,
): Promise<Area> {
  const query = new URLSearchParams({
    lat: String(latitude),
    lon: String(longitude),
  });
  const res = await fetch(
    `${API_BASE}/api/areas/${encodeURIComponent(municipalityCode)}?${query.toString()}`,
  );

  if (res.status === 404) {
    throw new AreaNotFoundError(municipalityCode);
  }
  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`);
  }

  return (await res.json()) as Area;
}
