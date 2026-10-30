import DesignSystemPage from "./DesignSystemPage";
import LandingPage from "./LandingPage";

export default function App() {
  const path = window.location.pathname;
  if (path === "/design-system") return <DesignSystemPage />;
  return <LandingPage />;
}
