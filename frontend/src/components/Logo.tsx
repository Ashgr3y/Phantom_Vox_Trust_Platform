import { AudioWaveform } from "lucide-react";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand-lockup" aria-label="Phantom Vox">
      <span className="brand-mark" aria-hidden="true">
        <AudioWaveform size={22} strokeWidth={2.2} />
      </span>
      {!compact && (
        <span className="brand-copy">
          <strong>Phantom Vox</strong>
          <small>Voice trust platform</small>
        </span>
      )}
    </div>
  );
}
