import { Link } from 'react-router-dom'
import { FOOTER_NAV } from '@/lib/site'

export default function SiteFooter({
  links = FOOTER_NAV,
  text = 'Local-first SRE operations. Your data stays on your machine or in your Supabase project.',
}) {
  return (
    <footer className="mt-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-16 sm:flex-row sm:items-end sm:justify-between sm:px-6">
        <p className="max-w-md text-sm leading-6 text-muted-foreground">{text}</p>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          {links.map((item) =>
            item.href ? (
              <a
                key={item.key || item.label}
                href={item.href}
                className="text-sm text-muted-foreground hover:text-foreground"
                target={item.external ? '_blank' : undefined}
                rel={item.external ? 'noopener noreferrer' : undefined}
              >
                {item.label}
              </a>
            ) : (
              <Link
                key={item.key || item.label}
                to={item.to}
                className="text-sm text-muted-foreground hover:text-foreground"
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
