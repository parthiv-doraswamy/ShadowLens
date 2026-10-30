import DashboardShell from "./DashboardShell";
import DesignSystemPage from "./DesignSystemPage";
import LandingPage from "./LandingPage";

export default function App() {
  const path = window.location.pathname;
  if (path === "/design-system") return <DesignSystemPage />;
  if (path === "/app" || path === "/app/") return <DashboardShell path="/app/overview" />;
  if (path.startsWith("/app/")) return <DashboardShell path={path} />;
  return <LandingPage />;
}
