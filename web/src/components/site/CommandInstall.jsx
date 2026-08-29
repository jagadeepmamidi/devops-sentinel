import { useState } from 'react'
import { INSTALL_COMMAND } from '@/lib/site'

export default function CommandInstall({
  command = INSTALL_COMMAND,
  note = 'Python 3.10+ · local-first · no account required',
}) {
  const [copied, setCopied] = useState(false)

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(command)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        className="flex max-w-full items-center gap-3 border border-border bg-black/20 px-3 py-2 font-mono text-[13px] tracking-normal normal-case"
        role="group"
        aria-label="Install command"
      >
        <span className="text-primary" aria-hidden="true">
          $
        </span>
        <code className="min-w-0 flex-1 overflow-x-auto text-foreground">{command}</code>
      </div>
      <div className="flex flex-wrap gap-3">
        <button type="button" className="btn-raw" onClick={copyCommand}>
          {copied ? 'COPIED' : 'INSTALL_SCRIPT'}
        </button>
      </div>
      {note ? <p className="text-[11px] tracking-[0.08em] text-muted-foreground">{note}</p> : null}
      <span className="sr-only" aria-live="polite">
        {copied ? `${command} copied to clipboard.` : ''}
      </span>
    </div>
  )
}
