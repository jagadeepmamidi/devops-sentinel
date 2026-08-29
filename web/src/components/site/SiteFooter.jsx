import { Link } from 'react-router-dom'
import { FOOTER_NAV } from '@/lib/site'

export default function SiteFooter({
  links = FOOTER_NAV,
  text = 'Local-first SRE operations. Your data stays on your machine or in your Supabase project.',
}) {
  return (
    <footer className="relative z-10 border-t border-border">
      <div className="page-wrap flex flex-col gap-4 py-8 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-xl text-xs leading-6 text-muted-foreground">{text}</p>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          {links.map((item) =>
            item.href ? (
              <a
                key={item.key || item.label}
                href={item.href}
                className="text-xs text-muted-foreground hover:text-foreground"
                target={item.external ? '_blank' : undefined}
                rel={item.external ? 'noopener noreferrer' : undefined}
              >
                {item.label}
              </a>
            ) : (
              <Link
                key={item.key || item.label}
                to={item.to}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                {item.label}
              </Link>
            ),
          )}
        </div>
      </div>
    </footer>
  )
}
