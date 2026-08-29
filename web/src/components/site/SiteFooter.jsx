import { Link } from 'react-router-dom'
import { FOOTER_NAV, GITHUB_URL } from '@/lib/site'

export default function SiteFooter({
  links = FOOTER_NAV,
  text = 'Local-first SRE. Your data stays on your machine or in your Supabase project.',
  hud = false,
}) {
  return (
    <footer className="relative z-10 border-t border-border">
      <div className="flex flex-col gap-4 px-4 py-6 sm:flex-row sm:items-end sm:justify-between sm:px-8">
        <p className="max-w-xl text-[11px] leading-6 tracking-[0.08em] text-muted-foreground">
          {text}
        </p>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
          {links.map((item) =>
            item.href ? (
              <a
                key={item.key || item.label}
                href={item.href}
                className="hud-link px-1 py-0.5 text-[11px] text-muted-foreground"
                target={item.external ? '_blank' : undefined}
                rel={item.external ? 'noopener noreferrer' : undefined}
              >
                {item.label}
              </a>
            ) : (
              <Link
                key={item.key || item.label}
                to={item.to}
                className="hud-link px-1 py-0.5 text-[11px] text-muted-foreground"
              >
                {item.label}
              </Link>
            ),
          )}
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border px-4 py-3 text-[11px] tracking-[0.12em] text-muted-foreground sm:px-8">
        <span>LOCAL · SELF-HOSTED · PYTHON</span>
        {hud ? (
          <span>
            <a
              className="hud-link px-1"
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
            >
              GITHUB
            </a>
            {'  '}© SENTINEL_SYS 2026
          </span>
        ) : (
          <span>© SENTINEL_SYS 2026</span>
        )}
      </div>
    </footer>
  )
}
