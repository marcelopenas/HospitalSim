import { useCallback, useEffect, useRef, useState } from 'react'

export const progressNotificationDuration = 5000
type Notification = { id: number; message: string; tone: 'info' | 'success' | 'error'; expiresAt?: number }

export function useNotifications() {
  const nextId = useRef(0)
  const [{ items, activeId }, setState] = useState<{ items: Notification[]; activeId: number | null }>({ items: [], activeId: null })
  function notify(message: string, tone: Notification['tone'] = 'success') {
    const item = { id: nextId.current++, message, tone, expiresAt: tone === 'info' ? Date.now() + progressNotificationDuration : undefined }
    setState(current => ({ items: [...current.items, item], activeId: item.id }))
  }
  const dismiss = useCallback((id: number) => {
    setState(current => {
      const index = current.items.findIndex(item => item.id === id)
      if (index === -1) return current
      const remaining = current.items.filter(item => item.id !== id)
      return { items: remaining, activeId: current.activeId === id ? remaining[Math.min(index, remaining.length - 1)]?.id ?? null : current.activeId }
    })
  }, [])
  useEffect(() => {
    const timers = items.flatMap(({ id, expiresAt }) => expiresAt === undefined ? [] : [window.setTimeout(() => dismiss(id), Math.max(0, expiresAt - Date.now()))])
    return () => timers.forEach(timer => window.clearTimeout(timer))
  }, [items, dismiss])
  const select = useCallback((id: number | null) => {
    setState(current => current.activeId === id ? current : { ...current, activeId: id })
  }, [])
  return { items, activeId, notify, dismiss, select }
}

