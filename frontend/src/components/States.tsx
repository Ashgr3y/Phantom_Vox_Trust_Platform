import { AlertTriangle, Inbox } from "lucide-react";

export function LoadingState({ lines = 4 }: { lines?: number }) {
  return <div className="skeleton-stack" aria-label="Loading">{Array.from({ length: lines }).map((_, index) => <span className="skeleton" key={index} />)}</div>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="empty-state"><Inbox size={30} /><strong>{title}</strong><p>{description}</p></div>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="empty-state error-state"><AlertTriangle size={30} /><strong>Something needs attention</strong><p>{message}</p>{onRetry && <button className="button secondary" onClick={onRetry}>Retry</button>}</div>;
}
