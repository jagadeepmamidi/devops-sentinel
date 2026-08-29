import { Link, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { GITHUB_URL, PRIMARY_NAV } from '@/lib/site'
import SiteBrand from './SiteBrand'

function NavItem({ item, className = '', onNavigate }) {
  const location = useLocation()
  const path = item.to?.split('#')[0]
  const active = Boolean(
    path &&
      (location.pathname === path ||
        (path !== '/' && location.pathname.startsWith(`${path}/`))),
  )

  const classes = ['hud-link px-1 py-0.5 text-[11px]', className].filter(Boolean).join(' ')

  if (item.href) {
    return (
      <a
        className={classes}
        href={item.href}
        target={item.external ? '_blank' : undefined}
        rel={item.external ? 'noopener noreferrer' : undefined}
        onClick={onNavigate}
      >
        {item.label}
      </a>
    )
  }

  return (
    <Link
      className={classes}
      to={item.to || '/'}
      aria-current={active ? 'page' : undefined}
      onClick={onNavigate}
    >
      {item.label}
    </Link>
  )
}

export default function SiteTopNav({ links = PRIMARY_NAV, brandTo = '/', hud = false }) {
  return (
    <header className={hud ? 'relative z-40' : 'sticky top-0 z-40 bg-background'}>
      <nav
        className={
          hud
            ? 'pointer-events-none absolute inset-x-0 top-0 z-40 hidden md:block'
            : 'mx-auto flex h-14 w-full items-center justify-between gap-4 border-b border-border px-4 sm:px-8'
        }
        aria-label="Primary navigation"
      >
        {hud ? (
          <>
            <div className="pointer-events-auto absolute top-8 left-20">
              <p className="text-[11px] tracking-[0.12em] text-muted-foreground">SYS.SENTINEL</p>
            </div>
            <div className="pointer-events-auto absolute top-8 right-20 flex items-center gap-5 text-[11px] tracking-[0.12em] text-muted-foreground">
              {links.map((item) => (
                <NavItem key={item.key || item.label} item={item} />
              ))}
            </div>
          </>
        ) : (
          <>
            <SiteBrand to={brandTo} />
            <div className="hidden items-center gap-5 md:flex">
              {links.map((item) => (
                <NavItem key={item.key || item.label} item={item} />
              ))}
            </div>
            <Sheet>
              <SheetTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="md:hidden"
                  aria-label="Open menu"
                >
                  <Menu className="size-4" />
                  Menu
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-72 border-border bg-background">
                <SheetHeader>
                  <SheetTitle>SENTINEL</SheetTitle>
                </SheetHeader>
                <Separator />
                <div className="flex flex-col gap-4 px-4">
                  {links.map((item) => (
                    <SheetClose asChild key={item.key || item.label}>
                      <NavItem item={item} className="text-sm" />
                    </SheetClose>
                  ))}
                </div>
              </SheetContent>
            </Sheet>
          </>
        )}
      </nav>
      {hud ? (
        <div className="flex h-14 items-center justify-between border-b border-border px-4 md:hidden">
          <SiteBrand to={brandTo} />
          <Sheet>
            <SheetTrigger asChild>
              <Button type="button" variant="outline" size="sm" aria-label="Open menu">
                <Menu className="size-4" />
                Menu
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-72 border-border bg-background">
              <SheetHeader>
                <SheetTitle>SENTINEL</SheetTitle>
              </SheetHeader>
              <Separator />
              <div className="flex flex-col gap-4 px-4">
                {links.map((item) => (
                  <SheetClose asChild key={item.key || item.label}>
                    <NavItem item={item} className="text-sm" />
                  </SheetClose>
                ))}
                <a className="hud-link px-1 py-0.5 text-sm" href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                  GitHub
                </a>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      ) : null}
    </header>
  )
}
