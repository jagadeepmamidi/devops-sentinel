export const INSTALL_COMMAND = 'pip install devops-sentinel-next'
export const GITHUB_URL = 'https://github.com/jagadeepmamidi/devops-sentinel'
export const GITHUB_ISSUES_URL = `${GITHUB_URL}/issues/new/choose`
export const PYPI_URL = 'https://pypi.org/project/devops-sentinel-next/'
export const SCHEMA_PATH = 'supabase/schema.sql'
export const DEMO_OK_PATH = '/api/demo/ok'
export const DEMO_FAIL_PATH = '/api/demo/fail'
export const DEMO_LIVE_PATH = '/api/demo/live'

export const PRIMARY_NAV = [
  { to: '/docs', label: 'Docs' },
  { to: '/docs#commands', label: 'CLI' },
  { to: '/about', label: 'About' },
  { href: GITHUB_URL, label: 'GitHub', external: true },
  { href: PYPI_URL, label: 'PyPI', external: true },
  { to: '/docs#quickstart', label: 'Install', className: 'outline' },
]

export const FOOTER_NAV = [
  { to: '/docs', label: 'Docs' },
  { to: '/about', label: 'About' },
  { href: PYPI_URL, label: 'PyPI', external: true },
  { to: '/privacy', label: 'Privacy' },
  { to: '/terms', label: 'Terms' },
  { to: '/feedback', label: 'Feedback' },
  { to: '/operator/services', label: 'Operator' },
]

export const OPERATOR_NAV = [
  { to: '/operator/services', label: 'Services' },
  { to: '/operator/incidents', label: 'Incidents' },
  { to: '/docs#operator', label: 'Docs' },
]
