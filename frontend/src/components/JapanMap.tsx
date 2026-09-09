import { useEffect, useRef } from "react";
import maplibregl, {
  type ExpressionSpecification,
  type StyleSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

interface JapanMapProps {
  selectedCode: string | null;
  onSelectMunicipality: (
    municipalityCode: string,
    latitude: number,
    longitude: number,
  ) => void;
}

// 国土数値情報 N03 から生成した全国市区町村ポリゴン（scripts/prepare_municipalities.py）
const GEOJSON_URL = "/data/municipalities.geojson";
const SOURCE_ID = "municipalities";
const FILL_LAYER_ID = "municipalities-fill";
const LINE_LAYER_ID = "municipalities-outline";

// 日本全国がおおむね収まる初期表示範囲（沖縄・離島・北海道を含む）
const JAPAN_BOUNDS: [number, number, number, number] = [122.0, 24.0, 154.0, 46.0];

const FILL_COLOR: ExpressionSpecification = [
  "case",
  ["boolean", ["feature-state", "selected"], false],
  "#e8622c",
  "#4a90d9",
];

/** 外部タイルに依存しない最小スタイル（オフラインでも表示できる）。 */
const BASE_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#eef3f8" },
    },
  ],
};

export function JapanMap({ selectedCode, onSelectMunicipality }: JapanMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const loadedRef = useRef(false);
  const prevSelectedRef = useRef<string | null>(null);

  // 初期化（マウント時に 1 回だけ）
  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: BASE_STYLE,
      bounds: JAPAN_BOUNDS,
      fitBoundsOptions: { padding: 16 },
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      // GeoJSON は MapLibre に URL で渡す（JS 側でパースしない）
      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: GEOJSON_URL,
        promoteId: "municipalityCode",
      });

      map.addLayer({
        id: FILL_LAYER_ID,
        type: "fill",
        source: SOURCE_ID,
        paint: { "fill-color": FILL_COLOR, "fill-opacity": 0.55 },
      });
      map.addLayer({
        id: LINE_LAYER_ID,
        type: "line",
        source: SOURCE_ID,
        paint: { "line-color": "#1f3a5f", "line-width": 0.4 },
      });

      map.on("click", FILL_LAYER_ID, (event) => {
        const code = event.features?.[0]?.properties?.municipalityCode;
        if (typeof code === "string") {
          // municipalityCode に加えてクリック地点の緯度経度も渡す
          onSelectMunicipality(code, event.lngLat.lat, event.lngLat.lng);
        }
      });
      map.on("mouseenter", FILL_LAYER_ID, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", FILL_LAYER_ID, () => {
        map.getCanvas().style.cursor = "";
      });

      loadedRef.current = true;
      applySelection(map, prevSelectedRef.current, selectedCode);
      prevSelectedRef.current = selectedCode;
    });

    return () => {
      loadedRef.current = false;
      map.remove();
      mapRef.current = null;
    };
    // selectedCode の変化は下の effect で扱う
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 選択状態の反映
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !loadedRef.current) return;
    applySelection(map, prevSelectedRef.current, selectedCode);
    prevSelectedRef.current = selectedCode;
  }, [selectedCode]);

  return <div className="japan-map" ref={containerRef} />;
}

function applySelection(
  map: maplibregl.Map,
  previous: string | null,
  next: string | null,
) {
  if (previous && previous !== next) {
    map.setFeatureState(
      { source: SOURCE_ID, id: previous },
      { selected: false },
    );
  }
  if (next) {
    map.setFeatureState({ source: SOURCE_ID, id: next }, { selected: true });
  }
}
