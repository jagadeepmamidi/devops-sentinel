import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'
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
    <div className="flex flex-col gap-2">
      <div
        className="flex max-w-full items-center gap-2 rounded-2xl border border-white/12 bg-white/[0.04] px-3 py-2 font-mono text-sm backdrop-blur-xl"
        role="group"
        aria-label="Install command"
      >
        <span className="text-primary" aria-hidden="true">
          $
        </span>
        <code className="min-w-0 flex-1 overflow-x-auto text-foreground">{command}</code>
        <Button type="button" variant="ghost" size="sm" onClick={copyCommand}>
          {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
      {note ? <p className="text-xs text-muted-foreground">{note}</p> : null}
      <span className="sr-only" aria-live="polite">
        {copied ? `${command} copied to clipboard.` : ''}
      </span>
    </div>
  )
}
