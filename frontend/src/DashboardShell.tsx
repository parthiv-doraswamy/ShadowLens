import { useState } from "react";

const navigation = [
  { section: "WORKSPACE", items: [
    { path: "/app/overview", label: "Overview", icon: "◫", description: "A consolidated view of AI activity, risk signals and collection coverage." },
    { path: "/app/inventory", label: "AI Inventory", icon: "▦", description: "Discover AI tools, providers, hosts and their observed activity." },
    { path: "/app/alerts", label: "Leak Alerts", icon: "⚑", description: "Review detection findings, masked evidence and triage status." },
    { path: "/app/graph", label: "Agent Graph", icon: "⌘", description: "Explore evidence-backed relationships between agents, tools and destinations." },
  ]},
  { section: "GOVERNANCE", items: [
    { path: "/app/compliance", label: "Compliance", icon: "▤", description: "Review framework mappings and informational control posture." },
    { path: "/app/ingest", label: "Data Sources", icon: "⇧", description: "Inspect supported inputs, ingestion capabilities and collection coverage." },
    { path: "/app/policies", label: "Policy Studio", icon: "⚙", description: "Validate and simulate candidate policies without activating them." },
  ]},
  { section: "SYSTEM", items: [
    { path: "/app/system", label: "System & Privacy", icon: "◈", description: "Understand local service health, privacy settings and visibility limitations." },
  ]},
];

const pages = navigation.flatMap(group => group.items);

export default function DashboardShell({ path }: { path: string }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const active = pages.find(page => page.path === path) ?? pages[0];

  return (
    <div className={`workspace ${collapsed ? "workspace--collapsed" : ""} ${mobileOpen ? "workspace--mobile-open" : ""}`}>
      <button className="workspace__scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />
      <aside className="workspace-sidebar" aria-label="Workspace navigation">
        <a className="workspace-brand" href="/" aria-label="ShadowLens home">
          <span className="workspace-brand__mark">S</span>
          <span className="workspace-brand__word">SHADOW<span>LENS</span></span>
        </a>
        <div className="workspace-sidebar__context">
          <span className="workspace-sidebar__context-mark">⌂</span>
          <span><strong>Local workspace</strong><small>Personal environment</small></span>
          <span className="workspace-sidebar__chevron">⌄</span>
        </div>
        <nav className="workspace-nav">
          {navigation.map(group => (
            <div className="workspace-nav__group" key={group.section}>
              <p className="workspace-nav__heading">{group.section}</p>
              {group.items.map(item => (
                <a key={item.path} href={item.path} title={collapsed ? item.label : undefined}
                  className={`workspace-nav__link ${active.path === item.path ? "is-active" : ""}`}
                  aria-current={active.path === item.path ? "page" : undefined}
                  onClick={() => setMobileOpen(false)}>
                  <span className="workspace-nav__icon" aria-hidden="true">{item.icon}</span>
                  <span className="workspace-nav__label">{item.label}</span>
                  {item.path === "/app/alerts" && <span className="workspace-nav__count" aria-label="No alert count available">—</span>}
                </a>
              ))}
            </div>
          ))}
        </nav>
        <div className="workspace-sidebar__bottom">
          <div className="workspace-privacy"><span className="workspace-privacy__icon">◇</span><div><strong>Local-first mode</strong><small>No cloud connection</small></div></div>
          <a className="workspace-sidebar__back" href="/">← <span>Back to website</span></a>
        </div>
      </aside>

      <div className="workspace-main">
        <header className="workspace-topbar">
          <div className="workspace-topbar__left">
            <button className="workspace-icon-button workspace-mobile-menu" aria-label="Open navigation" aria-expanded={mobileOpen} onClick={() => setMobileOpen(true)}>☰</button>
            <button className="workspace-icon-button workspace-collapse" aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"} aria-expanded={!collapsed} onClick={() => setCollapsed(value => !value)}>☷</button>
            <div className="workspace-breadcrumb"><span>Workspace</span><i>/</i><strong>{active.label}</strong></div>
          </div>
          <div className="workspace-topbar__right">
            <span className="workspace-preview-badge"><i /> PREVIEW ENVIRONMENT</span>
            <span className="workspace-user" aria-label="Local analyst profile">PA</span>
          </div>
        </header>

        <main className="workspace-content">
          <div className="workspace-page-heading">
            <div><p className="workspace-eyebrow">ANALYST WORKSPACE / {active.path.split("/").pop()?.toUpperCase()}</p><h1>{active.label}</h1><p>{active.description}</p></div>
            <span className="workspace-readiness"><i /> SHELL READY</span>
          </div>
          <section className="workspace-placeholder" aria-labelledby="workspace-placeholder-title">
            <div className="workspace-placeholder__symbol" aria-hidden="true">{active.icon}</div>
            <p className="workspace-eyebrow">WORKSPACE FOUNDATION</p>
            <h2 id="workspace-placeholder-title">{active.label} is ready for its page template.</h2>
            <p>The navigation, page frame and responsive workspace are in place. The detailed {active.label.toLowerCase()} interface is being added in the next frontend chunk.</p>
            <div className="workspace-placeholder__notice"><span>i</span><p><strong>Preview only.</strong> No backend API is connected and no live telemetry or findings are being displayed.</p></div>
            <a className="workspace-placeholder__link" href="/design-system">Review interface components <span>↗</span></a>
          </section>
          <footer className="workspace-footer"><span>SHADOWLENS / LOCAL-FIRST AI SECURITY</span><span>UI FOUNDATION 0.1</span></footer>
        </main>
      </div>
    </div>
  );
}
