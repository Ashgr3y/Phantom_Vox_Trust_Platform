export function ScoreBar({ value, label }: { value: number; label: string }) {
  const percent = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="score-bar-block">
      <div className="score-bar-label"><span>{label}</span><strong>{percent}</strong></div>
      <div className="score-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
        <span style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
