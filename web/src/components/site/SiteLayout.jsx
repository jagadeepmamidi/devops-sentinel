import SiteFooter from './SiteFooter'
import SiteTopNav from './SiteTopNav'

export default function SiteLayout({
  children,
  navLinks,
  footerLinks,
  footerText,
  mainClassName = '',
}) {
  return (
    <div className="relative flex min-h-[100dvh] flex-col overflow-x-hidden bg-background text-foreground">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(214,222,232,0.09),transparent_55%)]"
        aria-hidden="true"
      />
      <div className="site-grain" aria-hidden="true" />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[70] focus:rounded-full focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <div className="relative z-[40] flex min-h-[100dvh] flex-col">
        <SiteTopNav links={navLinks} />
        <main id="main-content" className={`flex-1 ${mainClassName}`.trim()}>
          {children}
        </main>
        <SiteFooter links={footerLinks} text={footerText} />
      </div>
    </div>
  )
}
