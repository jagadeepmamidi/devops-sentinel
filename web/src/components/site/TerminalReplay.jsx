const LINES = `DevOps Sentinel demo - local SQLite, no cloud, no API key.
Polling http://127.0.0.1:37037/fail once (expect 503)
demo-fail DOWN | 503 | 7ms

  INCIDENT OPENED
  id:       6b114ead-40f5-45b3-a95a-b33d35c7085e
  severity: high
  service:  demo-fail
  next:
    sentinel incidents show 6b114ead-40f5-45b3-a95a-b33d35c7085e
    sentinel postmortem generate 6b114ead-40f5-45b3-a95a-b33d35c7085e`

export default function TerminalReplay() {
  return (
    <pre
      className="m-0 overflow-x-auto rounded-2xl border border-white/10 bg-zinc-950/80 p-5 font-mono text-[13px] leading-7 text-zinc-200"
      aria-label="Sample sentinel demo session"
    >
      {LINES}
    </pre>
  )
}
