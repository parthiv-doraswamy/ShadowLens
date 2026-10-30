const signals = [
  { label: "Provider identity", value: "Corroborated", tier: "T1", tone: "good" },
  { label: "Flow behaviour", value: "Shape inferred", tier: "T2", tone: "warn" },
  { label: "Payload content", value: "Unavailable", tier: "—", tone: "muted" },
];

const capabilities = [
  { number: "01", title: "Discover the AI surface", body: "Build a local inventory of AI tools, providers, processes and destinations from supported endpoint signals." },
  { number: "02", title: "Detect sensitive-data exposure", body: "Apply deterministic, testable rules to authorized plaintext and structured events—with redacted evidence." },
  { number: "03", title: "Explain the risk", body: "Connect findings to their source, visibility tier and rule so analysts can understand what was observed and what was inferred." },
];

export default function LandingPage() {
  return (
    <main className="landing">
      <div className="landing-atmosphere" aria-hidden="true" />
      <header className="landing-nav">
        <a className="landing-brand" href="/" aria-label="ShadowLens home">
          <span className="landing-brand__mark">S</span>
          <span>SHADOW<span>LENS</span></span>
        </a>
        <nav className="landing-nav__links" aria-label="Main navigation">
          <a href="#platform">Platform</a>
          <a href="#visibility">Visibility model</a>
          <a href="#principles">Principles</a>
        </nav>
        <a className="landing-nav__action" href="/design-system">Interface preview <span aria-hidden="true">↗</span></a>
      </header>

      <section className="landing-hero">
        <div className="landing-hero__copy">
          <p className="landing-kicker"><span /> LOCAL-FIRST AI SECURITY OBSERVABILITY</p>
          <h1>See the AI<br /><em>you can’t</em><br />always see.</h1>
          <p className="landing-hero__lead">Understand where AI tools appear, how agents act, and where sensitive data may be exposed—without pretending encrypted traffic is transparent.</p>
          <div className="landing-hero__actions">
            <a className="landing-button landing-button--primary" href="#platform">Explore the platform <span aria-hidden="true">→</span></a>
            <a className="landing-button landing-button--quiet" href="#visibility">How visibility works</a>
          </div>
          <div className="landing-proof">
            <span className="landing-proof__rule" />
            <p>LOCAL-FIRST <b>·</b> EVIDENCE-LED <b>·</b> PRIVACY-CONSCIOUS</p>
          </div>
        </div>

        <div className="landing-visual" aria-label="Illustrative ShadowLens visibility overview">
          <div className="landing-visual__top">
            <span>OBSERVABILITY / 001</span><span className="landing-live"><i /> LOCAL SIGNALS</span>
          </div>
          <div className="landing-orbit" aria-hidden="true">
            <div className="landing-orbit__ring landing-orbit__ring--outer" />
            <div className="landing-orbit__ring landing-orbit__ring--middle" />
            <div className="landing-orbit__ring landing-orbit__ring--inner" />
            <div className="landing-orbit__cross landing-orbit__cross--h" />
            <div className="landing-orbit__cross landing-orbit__cross--v" />
            <span className="landing-orbit__node landing-orbit__node--one">AI</span>
            <span className="landing-orbit__node landing-orbit__node--two">↗</span>
            <span className="landing-orbit__node landing-orbit__node--three">···</span>
            <div className="landing-orbit__core"><span>SL</span><small>LOCAL<br />SENSOR</small></div>
          </div>
          <div className="landing-visual__caption"><span>VISIBILITY SNAPSHOT</span><span>ILLUSTRATIVE · NOT LIVE DATA</span></div>
          <div className="landing-signal-list">
            {signals.map((signal) => (
              <div className="landing-signal" key={signal.label}>
                <span className={`landing-signal__dot landing-signal__dot--${signal.tone}`} />
                <span className="landing-signal__label">{signal.label}</span>
                <span className="landing-signal__value">{signal.value}</span>
                <span className="landing-signal__tier">{signal.tier}</span>
              </div>
            ))}
          </div>
          <p className="landing-visual__footnote">Visibility depends on source, permissions and platform support.</p>
        </div>
        <div className="landing-hero__index" aria-hidden="true">01 / 04</div>
      </section>

      <section className="landing-strip" aria-label="Product principles">
        <span>01 / DISCOVER</span><span>02 / DETECT</span><span>03 / CORRELATE</span><span>04 / EXPLAIN</span>
      </section>

      <section className="landing-platform" id="platform">
        <div className="landing-section-head">
          <p className="landing-kicker">A CLEARER PICTURE OF AI RISK</p>
          <h2>From scattered signals<br />to <em>defensible insight.</em></h2>
          <p>ShadowLens brings endpoint metadata, authorized inspection and structured agent activity into one evidence-led workflow.</p>
        </div>
        <div className="landing-capabilities">
          {capabilities.map((item) => (
            <article className="landing-capability" key={item.number}>
              <span className="landing-capability__number">{item.number}</span>
              <div><h3>{item.title}</h3><p>{item.body}</p></div>
              <span className="landing-capability__arrow" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-visibility" id="visibility">
        <div>
          <p className="landing-kicker">TRUST THE SIGNAL, NOT THE ASSUMPTION</p>
          <h2>Every signal has<br />a <em>visibility level.</em></h2>
        </div>
        <div className="landing-visibility__tiers">
          <article><span>T1</span><div><h3>Observed metadata</h3><p>Process, destination and protocol metadata available from supported sources.</p></div></article>
          <article><span>T2</span><div><h3>Inferred behaviour</h3><p>Flow shape and patterns that suggest activity, clearly labelled as inference.</p></div></article>
          <article><span>T3</span><div><h3>Authorized plaintext</h3><p>Content inspection only where plaintext is legitimately available and explicitly supported.</p></div></article>
        </div>
      </section>

      <section className="landing-principles" id="principles">
        <p className="landing-kicker">BUILT AROUND RESTRAINT</p>
        <div className="landing-principles__grid">
          <h2>Security tooling<br />should earn your <em>trust.</em></h2>
          <ul>
            <li>Encrypted traffic is never described as content-inspected.</li>
            <li>Raw secrets and prompts are not persisted by default.</li>
            <li>Deterministic findings remain authoritative; AI advice is optional.</li>
            <li>Collection is local-first, least-privilege and transparent about gaps.</li>
          </ul>
        </div>
      </section>

      <footer className="landing-footer">
        <a className="landing-brand" href="/"><span className="landing-brand__mark">S</span><span>SHADOW<span>LENS</span></span></a>
        <p>LOCAL-FIRST AI SECURITY OBSERVABILITY</p>
        <a href="#top" onClick={(event) => { event.preventDefault(); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Back to top ↑</a>
      </footer>
    </main>
  );
}
