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
import { PRIMARY_NAV } from '@/lib/site'
import SiteBrand from './SiteBrand'

function NavItem({ item, className = '', onNavigate }) {
  const location = useLocation()
  const path = item.to?.split('#')[0]
  const active = Boolean(
    path &&
      (location.pathname === path ||
        (path !== '/' && location.pathname.startsWith(`${path}/`))),
  )

  const classes = [
    'text-sm text-muted-foreground transition-colors hover:text-foreground',
    item.className === 'outline'
      ? 'rounded-md border border-border bg-secondary/60 px-3 py-1.5 text-foreground hover:bg-secondary'
      : '',
    active ? 'text-foreground' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

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

export default function SiteTopNav({ links = PRIMARY_NAV, brandTo = '/' }) {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-background/55 backdrop-blur-xl">
      <nav
        className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6"
        aria-label="Primary navigation"
      >
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
          <SheetContent side="right" className="w-72">
            <SheetHeader>
              <SheetTitle>Sentinel</SheetTitle>
            </SheetHeader>
            <Separator />
            <div className="flex flex-col gap-4 px-4">
              {links.map((item) => (
                <SheetClose asChild key={item.key || item.label}>
                  <NavItem item={item} className="text-base" />
                </SheetClose>
              ))}
            </div>
          </SheetContent>
        </Sheet>
      </nav>
    </header>
  )
}
