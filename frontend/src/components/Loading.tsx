/** 詳細パネル内で使う小さなローディング表示。 */
export function Loading() {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="loading-spinner" aria-hidden="true" />
      <span>読み込み中...</span>
    </div>
  );
}
