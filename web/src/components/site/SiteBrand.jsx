import { Link } from "react-router-dom";
import BrandOrb from "../BrandOrb";

export default function SiteBrand({ to = "/" }) {
  return (
    <Link to={to} className="site-brand" aria-label="DevOps Sentinel home">
      <span className="site-brand-badge">
        <BrandOrb size="small" label="DevOps Sentinel logo" />
      </span>
      <span className="site-brand-text">DevOps Sentinel</span>
    </Link>
  );
}
