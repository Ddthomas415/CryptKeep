export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <div className="state loading">{label}</div>;
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="state empty">
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return <div className="state error">{message}</div>;
}
