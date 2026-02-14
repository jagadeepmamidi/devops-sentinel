import { Link } from 'react-router-dom'
import SiteBrand from './SiteBrand'

export default function SiteTopNav({ links = [], brandTo = '/' }) {
  return (
    <nav className="site-nav site-container">
      <SiteBrand to={brandTo} />
      <div className="site-nav-links">
        {links.map((item) => {
          if (item.href) {
            return (
              <a
                key={item.key || item.label}
                className={`site-nav-link ${item.className || ''}`.trim()}
                href={item.href}
                target={item.external ? '_blank' : undefined}
                rel={item.external ? 'noopener noreferrer' : undefined}
              >
                {item.label}
              </a>
            )
          }

          return (
            <Link
              key={item.key || item.label}
              className={`site-nav-link ${item.className || ''}`.trim()}
              to={item.to || '#'}
            >
              {item.label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
