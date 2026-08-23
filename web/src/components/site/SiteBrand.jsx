import { Link } from "react-router-dom";

export default function SiteBrand({ to = "/", onNavigate }) {
  return (
    <Link
      to={to}
      className="site-brand"
      aria-label="DevOps Sentinel home"
      onClick={onNavigate}
    >
      <span className="site-brand-mark" aria-hidden="true">
        S
      </span>
      <span className="site-brand-text">DevOps Sentinel</span>
    </Link>
  );
}
