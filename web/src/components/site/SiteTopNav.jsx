import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import SiteBrand from "./SiteBrand";

export default function SiteTopNav({ links = [], brandTo = "/" }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const menuId = "site-primary-navigation";

  const closeMenu = () => setMenuOpen(false);
  const isActive = (item) =>
    Boolean(
      item.to &&
        (location.pathname === item.to ||
          location.pathname.startsWith(`${item.to}/`)),
    );

  return (
    <nav className="site-nav site-container" aria-label="Primary navigation">
      <span className="site-nav-prompt" aria-hidden="true">
        sentinel@console:~$
      </span>
      <SiteBrand to={brandTo} onNavigate={closeMenu} />
      {links.length > 0 && (
        <button
          className="site-nav-toggle"
          type="button"
          aria-expanded={menuOpen}
          aria-controls={menuId}
          onClick={() => setMenuOpen((open) => !open)}
        >
          <span aria-hidden="true">{menuOpen ? "×" : "☰"}</span>
          <span>{menuOpen ? "Close" : "Menu"}</span>
        </button>
      )}
      <div
        id={menuId}
        className={`site-nav-links ${menuOpen ? "is-open" : ""}`.trim()}
      >
        {links.map((item) => {
          const active = isActive(item);
          const className = `site-nav-link ${item.className || ""} ${
            active ? "active" : ""
          }`.trim();

          if (item.href) {
            return (
              <a
                key={item.key || item.label}
                className={className}
                href={item.href}
                target={item.external ? "_blank" : undefined}
                rel={item.external ? "noopener noreferrer" : undefined}
                onClick={closeMenu}
              >
                {item.label}
              </a>
            );
          }

          return (
            <Link
              key={item.key || item.label}
              className={className}
              to={item.to || "/"}
              aria-current={active ? "page" : undefined}
              onClick={closeMenu}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
