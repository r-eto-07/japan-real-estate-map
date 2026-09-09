import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AreaDetailPanel } from "./AreaDetailPanel";
import type { Area } from "../types/area";

const sampleArea: Area = {
  municipalityCode: "12217",
  prefecture: "千葉県",
  city: "柏市",
  averageRent: 68200,
  rentYear: 2023,
  rentSource: "e-Stat 令和5年住宅・土地統計調査",
  landPricePerSqm: 165000,
  landPrice100sqm: 16500000,
  landPriceSource: "国土交通省 地価公示",
  landPriceYear: 2026,
  landPriceSampleCount: 4,
  transactionLandPricePerSqm: 178000,
  transactionLandPrice100sqm: 17800000,
  transactionSampleCount: 42,
  transactionPriceYear: 2025,
  transactionPriceSource: "国土交通省 不動産取引価格情報",
};

describe("AreaDetailPanel", () => {
  it("Area を渡すと家賃・地価公示・実取引を表示する", () => {
    render(<AreaDetailPanel area={sampleArea} loading={false} error={null} />);

    expect(screen.getByText(/柏市/)).toBeInTheDocument();
    expect(screen.getByText(/68,200円\/月/)).toBeInTheDocument();
    expect(screen.getByText("2023年")).toBeInTheDocument();
    expect(screen.getByText(/165,000円\/㎡/)).toBeInTheDocument();
    // 実取引
    expect(screen.getByText(/178,000円\/㎡/)).toBeInTheDocument();
    expect(screen.getByText(/17,800,000円/)).toBeInTheDocument();
    expect(screen.getByText(/42件 \/ 2025年/)).toBeInTheDocument();
    // 公示地価比 = round(178000 / 165000 * 100) = 108
    expect(screen.getByText("108%")).toBeInTheDocument();
  });

  it("実取引データが無いときは「取引データなし」を表示する", () => {
    render(
      <AreaDetailPanel
        area={{
          ...sampleArea,
          transactionLandPricePerSqm: null,
          transactionLandPrice100sqm: null,
          transactionPriceYear: null,
          transactionSampleCount: 0,
        }}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText("取引データなし")).toBeInTheDocument();
  });

  it("averageRent が null のときは「データなし」を表示する", () => {
    render(
      <AreaDetailPanel
        area={{ ...sampleArea, averageRent: null }}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText("データなし")).toBeInTheDocument();
    expect(screen.getByText("2023年")).toBeInTheDocument();
  });

  it("地価公示データが無い場合はその旨を表示する", () => {
    render(
      <AreaDetailPanel
        area={{
          ...sampleArea,
          landPricePerSqm: null,
          landPrice100sqm: null,
          landPriceYear: null,
          landPriceSampleCount: 0,
        }}
        loading={false}
        error={null}
      />,
    );

    expect(
      screen.getByText("周辺の地価公示データがありません"),
    ).toBeInTheDocument();
  });

  it("未選択時は案内メッセージを表示する", () => {
    render(<AreaDetailPanel area={null} loading={false} error={null} />);

    expect(
      screen.getByText("地図から地域を選択してください。"),
    ).toBeInTheDocument();
  });

  it("エラー時はエラーメッセージを表示する", () => {
    render(
      <AreaDetailPanel
        area={null}
        loading={false}
        error="地域情報を取得できませんでした。"
      />,
    );

    expect(
      screen.getByText("地域情報を取得できませんでした。"),
    ).toBeInTheDocument();
  });
});
