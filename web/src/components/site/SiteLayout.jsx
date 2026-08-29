import SiteFooter from './SiteFooter'
import SiteTopNav from './SiteTopNav'

export default function SiteLayout({
  children,
  navLinks,
  footerLinks,
  footerText,
  mainClassName = '',
  hud = false,
}) {
  return (
    <div className="relative flex min-h-[100dvh] flex-col bg-background font-mono text-foreground">
      <div className="site-noise" aria-hidden="true" />
      <div className="site-scanlines" aria-hidden="true" />
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:bg-foreground focus:px-3 focus:py-2 focus:text-background"
      >
        Skip to content
      </a>
      {hud ? (
        <>
          <span className="crosshair ch-tl hidden md:block" aria-hidden="true" />
          <span className="crosshair ch-tr hidden md:block" aria-hidden="true" />
          <span className="crosshair ch-bl hidden md:block" aria-hidden="true" />
          <span className="crosshair ch-br hidden md:block" aria-hidden="true" />
        </>
      ) : null}
      <SiteTopNav links={navLinks} hud={hud} />
      <main id="main-content" className={`relative z-10 flex-1 ${mainClassName}`.trim()}>
        {children}
      </main>
      <SiteFooter links={footerLinks} text={footerText} hud={hud} />
    </div>
  )
}
