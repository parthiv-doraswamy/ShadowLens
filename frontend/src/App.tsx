import DesignSystemPage from "./DesignSystemPage";

function BootstrapPage() {
  return (
    <main className="bootstrap">
      <p className="eyebrow">LOCAL-FIRST SECURITY AUDITING</p>
      <h1>ShadowLens</h1>
      <p className="message">
        Repository scaffold is ready. The interface foundation is being built independently
        of the backend contracts.
      </p>
      <span className="status">Bootstrap environment</span>
      <a className="bootstrap-link" href="/design-system">Open design system preview →</a>
    </main>
  );
}

export default function App() {
  return window.location.pathname === "/design-system" ? <DesignSystemPage /> : <BootstrapPage />;
}
