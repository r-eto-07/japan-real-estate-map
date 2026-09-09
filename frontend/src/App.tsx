import { useRef, useState } from "react";

import { AreaDetailPanel } from "./components/AreaDetailPanel";
import { JapanMap } from "./components/JapanMap";
import { AreaNotFoundError, getArea } from "./api/areaApi";
import type { Area } from "./types/area";

const ERROR_GENERIC = "地域情報を取得できませんでした。";
const ERROR_NOT_REGISTERED = "この地域のデータはまだ登録されていません。";

export default function App() {
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [area, setArea] = useState<Area | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);

  async function handleSelectMunicipality(
    municipalityCode: string,
    latitude: number,
    longitude: number,
  ) {
    if (inFlightRef.current) return; // クリック連打時の二重通信を防ぐ
    inFlightRef.current = true;

    setSelectedCode(municipalityCode);
    setLoading(true);
    setError(null);
    setArea(null);

    try {
      const result = await getArea(municipalityCode, latitude, longitude);
      setArea(result);
    } catch (err) {
      setArea(null);
      setError(
        err instanceof AreaNotFoundError ? ERROR_NOT_REGISTERED : ERROR_GENERIC,
      );
    } finally {
      setLoading(false);
      inFlightRef.current = false;
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1>不動産エリア分析</h1>
      </header>

      <main className="app__content">
        <div className="app__map">
          <JapanMap
            selectedCode={selectedCode}
            onSelectMunicipality={handleSelectMunicipality}
          />
        </div>
        <div className="app__detail">
          <AreaDetailPanel area={area} loading={loading} error={error} />
        </div>
      </main>
    </div>
  );
}
