import { useEffect, useState } from 'react'

export type ThemePreference = 'system' | 'light' | 'dark'
const storageKey = 'hospitalsim.theme'
const browserTheme = () => window.matchMedia('(prefers-color-scheme: dark)')
function savedPreference(): ThemePreference {
  try {
    const value = localStorage.getItem(storageKey)
    return value === 'light' || value === 'dark' ? value : 'system'
  } catch { return 'system' }
}
export function initializeTheme() {
  const preference = savedPreference()
  document.documentElement.dataset.theme = preference === 'dark' || (preference === 'system' && browserTheme().matches) ? 'dark' : 'light'
}
export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>(savedPreference)
  const [browserDark, setBrowserDark] = useState(() => browserTheme().matches)
  const dark = preference === 'dark' || (preference === 'system' && browserDark)
  useEffect(() => {
    const media = browserTheme()
    const update = () => setBrowserDark(media.matches)
    update()
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    try {
      if (preference === 'system') localStorage.removeItem(storageKey)
      else localStorage.setItem(storageKey, preference)
    } catch { /* The selected theme still works when browser storage is blocked. */ }
  }, [dark, preference])
  return { dark, preference, setPreference }
}
