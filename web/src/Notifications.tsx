import { useCallback, useLayoutEffect, useRef, useState } from 'react'
import { progressNotificationDuration } from './useNotifications'
import type { useNotifications } from './useNotifications'

function CountdownRing({ expiresAt }: { expiresAt: number }) {
  // Keep the animation's starting offset stable across carousel rerenders.
  const [delay] = useState(() => Math.min(0, expiresAt - Date.now() - progressNotificationDuration))
  return <svg className="notification-countdown" viewBox="0 0 32 32" aria-hidden="true"><circle className="notification-countdown-track" cx="16" cy="16" r="13"/><circle className="notification-countdown-progress" cx="16" cy="16" r="13" pathLength="1" style={{ animationDuration: `${progressNotificationDuration}ms`, animationDelay: `${delay}ms` }}/></svg>
}

export function Notifications({ items, activeId, dismiss, select }: Omit<ReturnType<typeof useNotifications>, 'notify'>) {
  const viewport = useRef<HTMLDivElement>(null)
  const pagination = useRef<HTMLElement>(null)
  const dotTouch = useRef<{ x: number; y: number } | null>(null)
  const wheel = useRef({ distance: 0, lastEvent: 0, lastSwitch: 0 })
  const previousCount = useRef(items.length)
  const index = Math.max(0, items.findIndex(item => item.id === activeId))
  const active = items[index]
  const move = useCallback((offset: number) => {
    const item = items[index + offset]
    if (item) select(item.id)
  }, [items, index, select])
  useLayoutEffect(() => {
    const element = viewport.current
    if (!element) return
    // Preserve the current card when older notifications expire.
    const instant = items.length < previousCount.current || window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let width = element.clientWidth
    element.scrollTo({ left: index * width, behavior: instant ? 'instant' : 'smooth' })
    const dots = pagination.current
    const selectedDot = dots?.querySelector<HTMLElement>('[aria-current=true]')
    if (dots && selectedDot) dots.scrollTo({ left: selectedDot.offsetLeft - (dots.clientWidth - selectedDot.clientWidth) / 2, behavior: instant ? 'instant' : 'smooth' })
    previousCount.current = items.length
    function scrollDots(event: WheelEvent) {
      if (event.ctrlKey) return
      const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY
      if (!delta) return
      const offset = delta > 0 ? 1 : -1
      if (!items[index + offset]) return
      event.preventDefault()
      const now = performance.now()
      const gesture = wheel.current
      if (now - gesture.lastEvent > 180 || Math.sign(gesture.distance) !== offset) gesture.distance = 0
      gesture.lastEvent = now
      gesture.distance += delta * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? width : 1)
      if (Math.abs(gesture.distance) >= 30 && now - gesture.lastSwitch >= 300) {
        gesture.distance = 0
        gesture.lastSwitch = now
        move(offset)
      }
    }
    dots?.addEventListener('wheel', scrollDots, { passive: false })
    const observer = new ResizeObserver(() => {
      if (element.clientWidth === width) return
      width = element.clientWidth
      element.scrollTo({ left: index * width, behavior: 'instant' })
    })
    observer.observe(element)
    return () => { observer.disconnect(); dots?.removeEventListener('wheel', scrollDots) }
  }, [items, index, move])
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
    <nav ref={pagination} className="notification-pagination" aria-label="Notification history" onTouchStart={event => { dotTouch.current = { x: event.touches[0].clientX, y: event.touches[0].clientY } }} onTouchEnd={event => {
      const start = dotTouch.current
      dotTouch.current = null
      if (!start) return
      const x = start.x - event.changedTouches[0].clientX
      const y = start.y - event.changedTouches[0].clientY
      if (Math.abs(x) > 40 && Math.abs(x) > Math.abs(y)) move(x > 0 ? 1 : -1)
    }} onTouchCancel={() => { dotTouch.current = null }}>{items.map((item, position) => <button type="button" key={item.id} className="notification-dot" aria-current={item.id === active.id ? 'true' : undefined} aria-label={`Notification ${position + 1} of ${items.length}: ${item.message}`} title={item.message} onClick={() => select(item.id)}><span/></button>)}</nav>
  </section>
}
