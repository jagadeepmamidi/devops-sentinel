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
    <div className="relative flex min-h-[100dvh] flex-col bg-background font-mono text-foreground">
      <div className="site-noise" aria-hidden="true" />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <SiteTopNav links={navLinks} />
      <main id="main-content" className={`relative z-10 flex-1 ${mainClassName}`.trim()}>
        {children}
      </main>
      <SiteFooter links={footerLinks} text={footerText} />
    </div>
  )
}
