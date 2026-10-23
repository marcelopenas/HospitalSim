import { useLayoutEffect, useRef, useState } from 'react'
import { progressNotificationDuration } from './useNotifications'
import type { useNotifications } from './useNotifications'

function CountdownRing({ expiresAt }: { expiresAt: number }) {
  // Keep the animation's starting offset stable across carousel rerenders.
  const [delay] = useState(() => Math.min(0, expiresAt - Date.now() - progressNotificationDuration))
  return <svg className="notification-countdown" viewBox="0 0 32 32" aria-hidden="true"><circle className="notification-countdown-track" cx="16" cy="16" r="13"/><circle className="notification-countdown-progress" cx="16" cy="16" r="13" pathLength="1" style={{ animationDuration: `${progressNotificationDuration}ms`, animationDelay: `${delay}ms` }}/></svg>
}

export function Notifications({ items, activeId, dismiss, select }: Omit<ReturnType<typeof useNotifications>, 'notify'>) {
  const viewport = useRef<HTMLDivElement>(null)
  const previousCount = useRef(items.length)
  const index = Math.max(0, items.findIndex(item => item.id === activeId))
  const active = items[index]
  useLayoutEffect(() => {
    const element = viewport.current
    if (!element) return
    // Preserve the current card when older notifications expire.
    const instant = items.length < previousCount.current || window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let width = element.clientWidth
    element.scrollTo({ left: index * width, behavior: instant ? 'instant' : 'smooth' })
    previousCount.current = items.length
    const observer = new ResizeObserver(() => {
      if (element.clientWidth === width) return
      width = element.clientWidth
      element.scrollTo({ left: index * width, behavior: 'instant' })
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [items.length, index])
  function move(offset: number) {
    const item = items[index + offset]
    if (item) select(item.id)
  }
  if (!active) return null
  return <section className="notifications" aria-label="Notifications" onKeyDown={event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault()
      move(event.key === 'ArrowLeft' ? -1 : 1)
    }
  }}>
    <div className="sr-only" role={active.tone === 'error' ? 'alert' : 'status'} aria-live={active.tone === 'error' ? 'assertive' : 'polite'} aria-atomic="true">{active.message}</div>
    <div ref={viewport} className="notification-viewport" role="group" aria-label="Notification messages. Scroll horizontally to browse." tabIndex={0} onScrollEnd={event => {
      const element = event.currentTarget
      if (!element.clientWidth) return
      const position = Math.max(0, Math.min(items.length - 1, Math.round(element.scrollLeft / element.clientWidth)))
      const item = items[position]
      if (item && item.id !== activeId) select(item.id)
    }}>
      <div className="notification-track">
        {items.map(item => <div key={item.id} className={`alert notification ${item.tone === 'info' ? '' : item.tone}`} aria-hidden={item.id !== active.id}>
          <p>{item.message}</p><button type="button" className="icon-button notification-close" aria-label={item.expiresAt ? 'Dismiss notification (automatically dismissed after 5 seconds)' : 'Dismiss notification'} title={item.expiresAt ? 'Automatically dismisses after 5 seconds' : 'Dismiss notification'} tabIndex={item.id === active.id ? 0 : -1} onClick={() => dismiss(item.id)}>{item.expiresAt && <CountdownRing expiresAt={item.expiresAt}/>}<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
        </div>)}
      </div>
    </div>
    <nav className="notification-pagination" aria-label="Notification history">{items.map((item, position) => <button type="button" key={item.id} className="notification-dot" aria-current={item.id === active.id ? 'true' : undefined} aria-label={`Notification ${position + 1} of ${items.length}: ${item.message}`} title={item.message} onClick={() => select(item.id)}><span/></button>)}</nav>
  </section>
}
