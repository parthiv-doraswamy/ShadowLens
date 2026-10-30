import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

export function Button({
  children,
  variant = "secondary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return <button className={`sl-button sl-button--${variant} sl-button--${size} ${className}`} {...props}>{children}</button>;
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "critical" | "info" }) {
  return <span className={`sl-badge sl-badge--${tone}`}><span className="sl-badge__dot" />{children}</span>;
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`sl-card ${className}`}>{children}</section>;
}

export function SectionHeading({ eyebrow, title, description }: { eyebrow?: string; title: string; description?: string }) {
  return <div className="sl-section-heading">{eyebrow && <p className="sl-eyebrow">{eyebrow}</p>}<h2>{title}</h2>{description && <p>{description}</p>}</div>;
}

export function TextField({ label, hint, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string }) {
  return <label className="sl-field"><span className="sl-field__label">{label}</span><input className="sl-input" {...props} />{hint && <span className="sl-field__hint">{hint}</span>}</label>;
}

export function SelectField({ label, children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: ReactNode }) {
  return <label className="sl-field"><span className="sl-field__label">{label}</span><select className="sl-input" {...props}>{children}</select></label>;
}

export function Tabs({ items, active, onChange }: { items: string[]; active: string; onChange: (value: string) => void }) {
  return <div className="sl-tabs" role="tablist" aria-label="Component examples">{items.map(item => <button key={item} type="button" role="tab" aria-selected={active === item} className={active === item ? "is-active" : ""} onClick={() => onChange(item)}>{item}</button>)}</div>;
}

export function StatusPanel({ kind, title, description, action }: { kind: "empty" | "error" | "loading" | "partial"; title: string; description: string; action?: ReactNode }) {
  return <div className={`sl-state sl-state--${kind}`} role={kind === "error" ? "alert" : "status"}>
    <span className="sl-state__mark" aria-hidden="true">{kind === "loading" ? "…" : kind === "error" ? "!" : kind === "partial" ? "◐" : "—"}</span>
    <div><strong>{title}</strong><p>{description}</p>{action && <div className="sl-state__action">{action}</div>}</div>
  </div>;
}

export function Dialog({ open, title, children, onClose }: { open: boolean; title: string; children: ReactNode; onClose: () => void }) {
  if (!open) return null;
  return <div className="sl-overlay" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <section className="sl-dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <div className="sl-dialog__head"><h3 id="dialog-title">{title}</h3><Button aria-label="Close dialog" variant="ghost" size="sm" onClick={onClose}>✕</Button></div>
      <div className="sl-dialog__body">{children}</div>
      <div className="sl-dialog__foot"><Button variant="secondary" onClick={onClose}>Close</Button></div>
    </section>
  </div>;
}

export function Drawer({ open, title, children, onClose }: { open: boolean; title: string; children: ReactNode; onClose: () => void }) {
  if (!open) return null;
  return <div className="sl-overlay sl-overlay--drawer" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <aside className="sl-drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      <div className="sl-dialog__head"><h3 id="drawer-title">{title}</h3><Button aria-label="Close drawer" variant="ghost" size="sm" onClick={onClose}>✕</Button></div>
      <div className="sl-dialog__body">{children}</div>
    </aside>
  </div>;
}
