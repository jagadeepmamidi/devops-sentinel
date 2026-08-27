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
    'rounded-full px-2.5 py-1.5 text-[13px] font-medium transition-colors',
    isCta
      ? 'bg-primary px-3.5 text-primary-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.45)] hover:bg-primary/90'
      : 'text-muted-foreground hover:bg-white/6 hover:text-foreground',
    !isCta && active ? 'bg-white/10 text-foreground' : '',
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
    <header className="sticky top-0 z-[40] flex justify-center px-3 pt-3">
      <nav
        className="glass-nav flex h-12 w-max max-w-[calc(100%-1.5rem)] flex-nowrap items-center gap-1 rounded-full border border-white/12 px-1.5 pl-2.5"
        aria-label="Primary navigation"
      >
        <SiteBrand to={brandTo} />

        <div className="hidden items-center gap-0.5 lg:flex">
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
              className="lg:hidden"
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
            <div className="flex flex-col gap-3 px-4">
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
