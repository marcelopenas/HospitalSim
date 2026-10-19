import { defaultAvatar } from './patientImage.ts'
export type Resource = 'hospitals' | 'roles' | 'staff' | 'patients'
export type Row = { id: number; [key: string]: string | number | null | number[] }
export type Database = Record<Resource, Row[]>
export type Payload = Record<string, string | number | null | (number | string)[]>
export type Initialization = { was_initialized: boolean }
export type ResponseData = Row | Row[] | Initialization | null
export type Request = {
  resource: Resource | 'initialization'; method: 'GET' | 'POST' | 'PATCH' | 'DELETE'; id?: number | string
  body?: Payload; title: string; bind?: string; hour?: number
}
export type Refs = Record<string, number>
export const resources: Resource[] = ['hospitals', 'roles', 'staff', 'patients']
export const emptyDatabase = (): Database => ({ hospitals: [], roles: [], staff: [], patients: [] })
export const readRequests = (): Request[] => resources.map(resource => ({ resource, method: 'GET', title: `Load ${resource}` }))
export const initializationRequest = (complete = false): Request => ({ resource: 'initialization', method: complete ? 'POST' : 'GET', title: complete ? 'Remember completed startup choice' : 'Check database initialization' })
export function isInitialization(result: ResponseData): result is Initialization {
  return !!result && !Array.isArray(result) && 'was_initialized' in result && typeof result.was_initialized === 'boolean'
}
export const sqlDisclaimer = 'Demo SQL example only. The browser sends HTTP requests with JSON, never SQL. The backend validates data and uses parameterized ORM queries; the SQL shown is an illustration of what will probably run, not an exact query log.'
const tables: Record<Resource, string> = { hospitals: 'hospital', roles: 'role', staff: 'staff', patients: 'patient' }
export function pathOf(request: Request): string {
  return `/${request.resource}${request.id === undefined ? '' : `/${request.id}`}`
}
export function resolveRequest(request: Request, refs: Refs): Request {
  const resolve = (value: string | number | null): string | number | null => {
    if (typeof value !== 'string' || !value.startsWith('$')) return value
    const id = refs[value.slice(1)]
    if (id === undefined) throw new Error(`Missing record reference: ${value}. Populate the demo first.`)
    return id
  }
  return { ...request,
    id: request.id === undefined ? undefined : resolve(request.id) as number,
    body: request.body && Object.fromEntries(Object.entries(request.body).map(([key, value]) => [key, Array.isArray(value) ? value.map(resolve) : resolve(value)])),
  } as Request
}
function literal(value: unknown): string {
  if (value === null) return 'NULL'
  if (typeof value === 'number') return String(value)
  if (typeof value === 'string' && value.startsWith('$')) return `:${value.slice(1)}_id`
  return `'${String(value).replaceAll('\\', '\\\\').replaceAll("'", "''")}'`
}
export function sqlFor(request: Request, writesOnly = false): string {
  if (request.resource === 'initialization') return request.method === 'GET'
    ? 'SELECT was_initialized FROM app_state WHERE id = 1; -- no row means false'
    : 'INSERT INTO app_state (id, was_initialized) VALUES (1, TRUE)\nON DUPLICATE KEY UPDATE was_initialized = TRUE;\nCOMMIT;'
  const table = tables[request.resource]
  const id = literal(request.id)
  const fields = Object.entries(request.body ?? {}).filter(([key]) => key !== 'role_ids')
  if (request.resource === 'patients' && request.method === 'POST' && !fields.some(([key]) => key === 'image_blob')) fields.push(['image_blob', defaultAvatar])
  const sqlValue = (key: string, value: unknown) => key === 'image_blob' ? `FROM_BASE64(${literal(value ?? defaultAvatar)})` : literal(value)
  const checks: string[] = []
  const writes: string[] = []
  if (request.method === 'GET') return `SELECT * FROM ${table}${request.id === undefined ? '' : ` WHERE id = ${id}`};${request.resource === 'staff' ? '\nSELECT staff_id, role_id FROM staff_roles; -- load role assignments' : ''}`
  if (request.method !== 'POST') checks.push(`SELECT * FROM ${table} WHERE id = ${id};`)
  if (request.body?.hospital_id !== undefined) checks.push(`SELECT * FROM hospital WHERE id = ${literal(request.body.hospital_id)};`)
  if (request.resource === 'patients' && (request.method === 'POST' || request.method === 'PATCH')) checks.push('SELECT capacity FROM hospital WHERE id = :resulting_hospital_id FOR UPDATE;', 'SELECT COUNT(*) FROM patient WHERE hospital_id = :resulting_hospital_id; -- exclude this patient on PATCH; reject if full')
  if (request.resource === 'hospitals' && request.method === 'PATCH' && request.body?.capacity !== undefined) checks.push(`SELECT COUNT(*) FROM patient WHERE hospital_id = ${id}; -- capacity must cover existing patients`)
  if (request.body?.staff_id != null) checks.push(`SELECT * FROM staff WHERE id = ${literal(request.body.staff_id)}; -- validate same hospital`)
  if (request.resource === 'roles' && request.body?.name) checks.push(`SELECT * FROM role WHERE name = ${literal(request.body.name)}; -- uniqueness check`)
  if (request.resource === 'hospitals' && request.body) checks.push('/* Backend checks unique hospital name and location. */')
  if (request.resource === 'staff' && request.method === 'PATCH' && request.body?.hospital_id !== undefined) checks.push(`SELECT id FROM patient WHERE staff_id = ${id}; -- block transfer if patients remain`)
  if (request.method === 'DELETE') {
    if (request.resource === 'hospitals') checks.push(`SELECT id FROM staff WHERE hospital_id = ${id};`, `SELECT id FROM patient WHERE hospital_id = ${id}; -- reject if dependents exist`)
    if (request.resource === 'roles') checks.push(`SELECT staff_id FROM staff_roles WHERE role_id = ${id}; -- reject assigned role`)
    if (request.resource === 'staff') {
      checks.push(`SELECT id FROM patient WHERE staff_id = ${id}; -- reject assigned staff`)
      writes.push(`DELETE FROM staff_roles WHERE staff_id = ${id};`)
    }
    writes.push(`DELETE FROM ${table} WHERE id = ${id};`)
  } else {
    if (request.method === 'POST') writes.push(`INSERT INTO ${table} (${fields.map(([key]) => key).join(', ')})\nVALUES (${fields.map(([key, value]) => sqlValue(key, value)).join(', ')});`)
    else if (fields.length) writes.push(`UPDATE ${table} SET ${fields.map(([key, value]) => `${key} = ${sqlValue(key, value)}`).join(', ')}\nWHERE id = ${id};`)
    const roles = request.body?.role_ids
    if (Array.isArray(roles)) {
      const staff = request.method === 'POST' ? ':created_staff_id' : id
      if (roles.length) checks.unshift(`SELECT * FROM role WHERE id IN (${roles.map(literal).join(', ')});`)
      if (request.method === 'PATCH') writes.push(`DELETE FROM staff_roles WHERE staff_id = ${staff};`)
      for (const role of roles) writes.push(`INSERT INTO staff_roles (staff_id, role_id) VALUES (${staff}, ${literal(role)});`)
    }
  }
  return [writesOnly ? '-- Planned writes; validation reads are separate.' : '-- Illustrative checks and writes; not exact ORM statement order.', ...(writesOnly ? [] : checks), ...writes, 'COMMIT; -- only if validation succeeds'].join('\n')
}
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}
export async function send(request: Request, base = '/api', fetcher: typeof fetch = fetch): Promise<ResponseData> {
  let response: Response
  try {
    response = await fetcher(`${base.replace(/\/$/, '')}${pathOf(request)}`, {
      method: request.method, headers: request.body ? { 'Content-Type': 'application/json' } : undefined,
      body: request.body ? JSON.stringify(request.body) : undefined,
      // Reviews, post-write refreshes, and demo checks must read the actual backend.
      // Other API clients can use the server's resource-specific cache lifetimes.
      cache: request.method === 'GET' ? 'no-store' : undefined,
      signal: AbortSignal.timeout(20000),
    })
  } catch {
    throw new Error('Cannot reach the API, or the request timed out. Check the API connection and refresh before retrying: a timed-out write may have committed.')
  }
  if (!response.ok) {
    const text = await response.text()
    let detail = text
    try { const parsed = JSON.parse(text); detail = typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail ?? parsed) } catch { /* Preserve non-JSON server errors. */ }
    throw new ApiError(response.status, `${response.status}: ${detail.slice(0, 1000)}`)
  }
  if (response.status === 204) return null
  try { return await response.json() } catch { throw new Error('The API returned an invalid JSON response. Check the API proxy configuration.') }
}
export function applyResponse(data: Database, request: Request, result: ResponseData): Database {
  if (request.resource === 'initialization') {
    if (!isInitialization(result)) throw new Error('Invalid initialization response. Rebuild the backend and refresh.')
    return data
  }
  if (request.method === 'GET' && request.id === undefined) {
    if (!Array.isArray(result)) throw new Error('Expected a list from the API. Check the API URL.')
    return { ...data, [request.resource]: result }
  }
  if (request.method === 'GET') return data
  if (request.method === 'DELETE') return { ...data, [request.resource]: data[request.resource].filter(row => row.id !== request.id) }
  if (!result || Array.isArray(result) || !('id' in result) || !Number.isInteger(result.id)) throw new Error('Expected a saved record from the API.')
  const rows = data[request.resource].filter(row => row.id !== result.id)
  return { ...data, [request.resource]: [...rows, result].sort((a, b) => a.id - b.id) }
}
export async function runRequests(requests: Request[], refs: Refs, execute: (request: Request) => Promise<ResponseData>): Promise<void> {
  for (const item of requests) {
    const result = await execute(resolveRequest(item, refs))
    if (item.bind) {
      if (!result || Array.isArray(result) || !('id' in result)) throw new Error('Missing created record ID.')
      refs[item.bind] = result.id
    }
  }
}
