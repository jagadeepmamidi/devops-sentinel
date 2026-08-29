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
  const isCta = item.className === 'outline'

  const classes = [
    isCta
      ? 'inline-flex h-8 items-center border border-border px-3 text-xs font-medium text-foreground hover:border-foreground hover:bg-secondary'
      : 'text-sm text-muted-foreground transition-colors hover:text-foreground',
    active && !isCta ? 'text-foreground' : '',
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
    <header className="sticky top-0 z-40 border-b border-border bg-background/92 backdrop-blur-sm">
      <nav
        className="page-wrap flex h-14 items-center justify-between gap-4"
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
          <SheetContent side="right" className="w-72 border-border bg-background">
            <SheetHeader>
              <SheetTitle>sentinel</SheetTitle>
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
