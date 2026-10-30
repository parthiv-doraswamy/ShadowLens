import { useState } from "react";
import { Badge, Button, Card, Dialog, Drawer, SectionHeading, SelectField, StatusPanel, Tabs, TextField } from "./design-system/components";

const palette = [
  ["Obsidian", "#111820", "Primary canvas"],
  ["Warm paper", "#EAE8E0", "Light surface"],
  ["Deep forest", "#244C48", "Primary action"],
  ["Muted amber", "#C58B45", "Attention accent"],
  ["Slate", "#65747D", "Secondary text"],
  ["Border", "#D4D5CE", "Dividers"],
  ["Critical", "#A7473D", "High severity"],
  ["Success", "#48765D", "Healthy state"],
];

export default function DesignSystemPage() {
  const [activeTab, setActiveTab] = useState("Buttons");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filter, setFilter] = useState("All severities");
  const [query, setQuery] = useState("");

  return <main className="ds-page">
    <header className="ds-topbar">
      <a className="ds-brand" href="/" aria-label="ShadowLens home"><span className="ds-brand__mark">S</span><span>SHADOW<span>LENS</span></span></a>
      <div className="ds-topbar__meta"><Badge tone="success">Design system</Badge><a href="/">Back to app</a></div>
    </header>
    <div className="ds-layout">
      <aside className="ds-sidebar">
        <p className="ds-sidebar__label">FOUNDATIONS</p>
        <a className="is-current" href="#foundations">Colour & type</a>
        <a href="#components">Components</a>
        <a href="#feedback">Feedback states</a>
        <a href="#patterns">Interaction patterns</a>
        <div className="ds-sidebar__note"><span className="ds-sidebar__line" />Local-first by design</div>
      </aside>
      <div className="ds-content">
        <div className="ds-page-intro">
          <div><p className="sl-eyebrow">FOUNDATION / 01</p><h1>Interface system</h1><p>A practical component language for security teams. Quiet confidence, clear evidence, no theatre.</p></div>
          <Badge tone="warning">Preview · no API connection</Badge>
        </div>

        <section id="foundations" className="ds-section">
          <SectionHeading eyebrow="01 / FOUNDATIONS" title="Colour with a purpose" description="A restrained palette built for long analyst sessions and high-signal status communication." />
          <div className="ds-swatches">{palette.map(([name, hex, use]) => <div className="ds-swatch" key={name}><div className="ds-swatch__color" style={{ backgroundColor: hex }} /><div className="ds-swatch__meta"><strong>{name}</strong><code>{hex}</code><span>{use}</span></div></div>)}</div>
          <Card className="ds-type-card"><div><p className="sl-eyebrow">DISPLAY / 48</p><h2 className="ds-type-display">See the whole<br/>attack surface.</h2></div><div className="ds-type-copy"><p className="sl-eyebrow">BODY / 15</p><p>ShadowLens helps teams discover AI usage, understand data exposure and govern agent activity without pretending encrypted traffic is visible.</p><span className="ds-muted">Interface copy · 15px / 1.65</span></div></Card>
        </section>

        <section id="components" className="ds-section">
          <SectionHeading eyebrow="02 / COMPONENTS" title="Reusable building blocks" description="Consistent interaction patterns for dense, evidence-oriented workflows." />
          <Card>
            <Tabs items={["Buttons", "Badges", "Forms", "Table"]} active={activeTab} onChange={setActiveTab} />
            {activeTab === "Buttons" && <div className="ds-component-row"><Button variant="primary">Primary action</Button><Button variant="secondary">Secondary</Button><Button variant="ghost">Quiet action</Button><Button variant="danger">Destructive</Button><Button size="sm">Compact</Button><Button size="lg">Large action</Button><Button disabled>Disabled</Button></div>}
            {activeTab === "Badges" && <div className="ds-component-row"><Badge>Unclassified</Badge><Badge tone="success">Healthy</Badge><Badge tone="warning">Needs review</Badge><Badge tone="critical">Critical</Badge><Badge tone="info">Informational</Badge></div>}
            {activeTab === "Forms" && <div className="ds-form-grid"><TextField label="Search inventory" placeholder="Search by provider or host" value={query} onChange={event => setQuery(event.target.value)} hint="Search is local to this component preview."/><SelectField label="Severity filter" value={filter} onChange={event => setFilter(event.target.value)}><option>All severities</option><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></SelectField><label className="sl-check"><input type="checkbox" defaultChecked/><span>Include provisional endpoints</span></label><Button variant="primary" onClick={() => { setQuery(""); setFilter("All severities"); }}>Reset filters</Button></div>}
            {activeTab === "Table" && <div className="ds-table-wrap"><table className="sl-table"><thead><tr><th>Provider</th><th>Visibility</th><th>Confidence</th><th>Status</th></tr></thead><tbody><tr><td>OpenAI API</td><td><Badge tone="info">T1 · Metadata</Badge></td><td>High</td><td><Badge tone="success">Known</Badge></td></tr><tr><td>Local model</td><td><Badge tone="warning">T2 · Inferred</Badge></td><td>Medium</td><td><Badge tone="warning">Provisional</Badge></td></tr><tr><td>Unknown host</td><td><Badge>T1 · Metadata</Badge></td><td>Low</td><td><Badge>Unclassified</Badge></td></tr></tbody></table><p className="ds-demo-caption">Illustrative component data — not observed telemetry.</p></div>}
          </Card>
        </section>

        <section id="feedback" className="ds-section">
          <SectionHeading eyebrow="03 / FEEDBACK" title="Make system state explicit" description="Loading, empty, error and partial-coverage states are first-class interface components." />
          <div className="ds-state-grid">
            <Card><StatusPanel kind="loading" title="Loading inventory" description="Waiting for the local service to respond." /></Card>
            <Card><StatusPanel kind="empty" title="No findings yet" description="No matching findings are available for this filter." action={<Button size="sm">Clear filters</Button>} /></Card>
            <Card><StatusPanel kind="error" title="Could not load events" description="The local API did not respond. Existing evidence has not been changed." action={<Button size="sm" variant="secondary">Retry</Button>} /></Card>
            <Card><StatusPanel kind="partial" title="Partial visibility" description="Process attribution is unavailable. Network metadata may still be collected." /></Card>
          </div>
        </section>

        <section id="patterns" className="ds-section">
          <SectionHeading eyebrow="04 / INTERACTION" title="Dialogs, drawers and tooltips" description="Use focused overlays for confirmation and contextual detail. Keep keyboard focus visible." />
          <Card className="ds-pattern-card"><div><strong>Confirmation dialog</strong><p>For consequential actions that require a deliberate decision.</p><Button variant="primary" onClick={() => setDialogOpen(true)}>Open dialog</Button></div><div><strong>Context drawer</strong><p>For evidence details without losing the current page context.</p><Button onClick={() => setDrawerOpen(true)}>Open drawer</Button></div><div><strong>Tooltip</strong><p>Supplementary context, never the only place essential information lives.</p><button className="sl-tooltip" type="button" title="This is supplementary context.">Hover or focus for context ⓘ</button></div></Card>
        </section>

        <footer className="ds-footer"><span>SHADOWLENS / DESIGN SYSTEM 0.1</span><span>Local-first · Evidence-led · Privacy-aware</span></footer>
      </div>
    </div>
    <Dialog open={dialogOpen} title="Confirm example action" onClose={() => setDialogOpen(false)}><p>This is a demonstration dialog. No data or configuration will be changed.</p></Dialog>
    <Drawer open={drawerOpen} title="Evidence context" onClose={() => setDrawerOpen(false)}><Badge tone="info">T1 · Metadata</Badge><h4>Visibility is limited by source</h4><p>Encrypted HTTPS payload content is not visible in this metadata-only view. The interface must communicate that limitation clearly.</p><dl className="ds-detail-list"><dt>Source</dt><dd>Local network metadata</dd><dt>Evidence status</dt><dd>Observed metadata</dd><dt>Payload</dt><dd>Unavailable</dd></dl></Drawer>
  </main>;
}
