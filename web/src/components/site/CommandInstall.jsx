import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { INSTALL_COMMAND } from '@/lib/site'

export default function CommandInstall({
  command = INSTALL_COMMAND,
  note = 'Python 3.10+. Local-first. No account required.',
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
    <div className="flex w-fit max-w-full flex-col gap-2">
      <div
        className="inline-flex max-w-full items-center gap-2.5 rounded-full border border-white/14 bg-[linear-gradient(180deg,rgba(255,255,255,0.08),rgba(255,255,255,0.02))] py-1.5 pl-4 pr-1.5 font-mono text-[13px] shadow-[inset_0_1px_0_rgba(255,255,255,0.16)]"
        role="group"
        aria-label="Install command"
      >
        <span className="text-primary" aria-hidden="true">
          $
        </span>
        <code className="min-w-0 truncate text-foreground">{command}</code>
        <button
          type="button"
          onClick={copyCommand}
          className="inline-flex size-8 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/8 text-zinc-200 transition-colors hover:bg-white/14 hover:text-white active:scale-[0.98]"
          aria-label={copied ? 'Copied' : 'Copy install command'}
        >
          {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
        </button>
      </div>
      {note ? <p className="text-xs text-muted-foreground">{note}</p> : null}
      <span className="sr-only" aria-live="polite">
        {copied ? `${command} copied to clipboard.` : ''}
      </span>
    </div>
  )
}
