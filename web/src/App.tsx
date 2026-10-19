import { useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { applyResponse, emptyDatabase, initializationRequest, isInitialization, pathOf, readRequests, resolveRequest, runRequests, send, sqlDisclaimer, sqlFor } from './api'
import type { Database, Payload, Refs, Request, Resource, Row } from './api'
import { baselineRefs, baselineProblems, fingerprint, populationPlan, testPlan, finalStateMatches } from './demo'
import { useTheme } from './useTheme'
import { avatarSource, defaultAvatar, uploadAvatar } from './patientImage'
import './App.css'
import './theme.css'

function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    users: <><circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6M21 21v-3a6 6 0 0 0-3-5"/></>,
    hospital: <><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M12 6v6M9 9h6M9 21v-5h6v5"/></>,
    heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>,
    pulse: <path d="M2 12h5l3-8 4 16 3-8h5"/>,
    book: <><path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1ZM12 5v15"/></>,
    arrow: <path d="M7 17 17 7M7 7h10v10"/>,
    code: <><path d="m8 7-5 5 5 5m8-10 5 5-5 5m-3-14-2 18"/></>,
    play: <path d="m8 4 12 8-12 8Z"/>, pause: <><path d="M8 4v16M16 4v16"/></>,
    reset: <><path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/></>,
    plus: <path d="M12 5v14M5 12h14"/>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    search: <><circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/></>,
    bed: <><path d="M3 5v15m18-9v9M3 16h18M3 11h18v5M6 8h5v3H6Z"/></>,
    chevron: <path d="m9 5 7 7-7 7"/>,
    check: <path d="m5 12 4 4L19 6"/>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] ?? paths.pulse}</svg>
}
const apiBase = import.meta.env.VITE_API_URL || '/api'
const swaggerUrl = import.meta.env.VITE_SWAGGER_URL || (apiBase.startsWith('http') ? `${apiBase.replace(/\/$/, '')}/docs` : `http://${window.location.hostname}:8080/docs`)
const labels: Record<Resource, string> = { hospitals: 'Hospitals', roles: 'Roles', staff: 'Staff', patients: 'Patients' }
type Page = 'Overview' | Resource | 'Testing'
type Review = { title: string; description: string; requests: Request[]; reads?: Request[]; writesOnly?: boolean; confirm: string; action: () => Promise<void> }
type Log = { request: Request; status: string; detail?: string }
type TestRun = { requests: Request[]; refs: Refs; index: number; failed?: boolean }
function SqlNote() { return <p className="sql-note">{sqlDisclaimer}</p> }
function Preview({ requests, expanded = false, writesOnly = false }: { requests: Request[]; expanded?: boolean; writesOnly?: boolean }) {
  return <div className="request-previews"><SqlNote/>{requests.map((item, i) => <details key={i} open={expanded || undefined}><summary><b>{item.method}</b> {pathOf(item)} <span>{item.title}</span></summary>{item.body && <pre>{JSON.stringify(item.body, null, 2)}</pre>}<pre>{sqlFor(item, writesOnly)}</pre></details>)}</div>
}
function Dialog({ title, close, children }: { title: string; close: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null)
  const backdropPress = useRef(false)
  useEffect(() => { ref.current?.showModal() }, [])
  function outside(event: { target: EventTarget; currentTarget: HTMLDialogElement; clientX: number; clientY: number }) {
    if (event.target !== event.currentTarget) return false
    const bounds = event.currentTarget.getBoundingClientRect()
    return event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom
  }
  return <dialog ref={ref} onPointerDown={event => { backdropPress.current = event.button === 0 && outside(event) }} onClick={event => {
    const cancel = backdropPress.current && outside(event)
    backdropPress.current = false
    if (cancel) close()
  }} onCancel={event => { event.preventDefault(); close() }}><div className="modal-heading"><h2>{title}</h2><button type="button" className="icon-button" aria-label="Close dialog" onClick={close}>×</button></div>{children}</dialog>
}
const nameOf = (row?: Row) => row ? String(row.name ?? `${row.first_name} ${row.last_name}`) : 'Unassigned'
function Editor({ resource, row, data, close, save }: { resource: Resource; row?: Row; data: Database; close: () => void; save: (request: Request) => void }) {
  const initial: Payload = resource === 'hospitals' ? { name: '', location: '', capacity: 100 } : resource === 'roles' ? { name: '', description: null, access_type: 'C' } : resource === 'staff' ? { first_name: '', last_name: '', date_of_admission: '', last_check_in: null, salary: '0.00', hospital_id: Number(data.hospitals[0]?.id) || 0, role_ids: [] } : { first_name: '', last_name: '', date_of_birth: '', image_blob: defaultAvatar, hospital_id: Number(data.hospitals[0]?.id) || 0, staff_id: null }
  const [body, setBody] = useState<Payload>(row ? Object.fromEntries(Object.keys(initial).map(key => [key, row[key]])) : initial)
  const [imageError, setImageError] = useState('')
  const [imageBusy, setImageBusy] = useState(false)
  const request: Request = { resource, method: row ? 'PATCH' : 'POST', id: row?.id, body, title: `${row ? 'Update' : 'Create'} ${resource} record` }
  function submit(event: FormEvent) { event.preventDefault(); if (!imageBusy && !imageError) save(request) }
  return <Dialog title={request.title} close={close}><form onSubmit={submit}>
    <p>Values are sent to the FastAPI CRUD endpoint and saved in MySQL after validation.</p>
    {Object.entries(body).map(([key, value]) => key === 'image_blob' ? <fieldset className="image-editor" key={key}><legend>Patient profile image (optional)</legend><img className="patient-avatar large" src={avatarSource(value)} alt="Patient profile preview"/><div><label>Upload custom image<input type="file" accept="image/png,image/jpeg,image/webp" disabled={imageBusy} onChange={async event => {
      const file = event.currentTarget.files?.[0]
      event.currentTarget.value = ''
      if (!file) return
      setImageError(''); setImageBusy(true)
      try { const image = await uploadAvatar(file); setBody(current => ({ ...current, image_blob: image })) } catch (cause) { setImageError(cause instanceof Error ? cause.message : 'The image could not be opened.') } finally { setImageBusy(false) }
    }}/></label><button type="button" className="text-button" disabled={imageBusy} onClick={() => { setBody(current => ({ ...current, image_blob: defaultAvatar })); setImageError('') }}>Use default profile</button><p className="muted">PNG, JPEG, or WebP up to 5 MB. The browser prepares a small profile image before sending it; MySQL stores the image bytes in a BLOB.</p>{imageBusy && <p role="status">Preparing image…</p>}{imageError && <p role="alert" className="danger">{imageError}</p>}</div></fieldset> : key === 'access_type' ? <label key={key}>access type<select required value={String(value)} onChange={event => setBody(current => ({ ...current, access_type: event.target.value }))}>{['A', 'B', 'C'].map(type => <option key={type} value={type}>{type}</option>)}</select></label> : key === 'role_ids' ? <fieldset key={key}><legend>Roles</legend>{data.roles.length ? data.roles.map(role => <label className="checkbox-label" key={role.id}><input type="checkbox" checked={Array.isArray(value) && value.includes(role.id)} onChange={event => setBody(current => ({ ...current, role_ids: event.target.checked ? [...(current.role_ids as number[]), role.id] : (current.role_ids as number[]).filter(id => id !== role.id) }))}/>{nameOf(role)}</label>) : <p>No roles exist yet. Staff may have no roles.</p>}</fieldset> : key === 'hospital_id' || key === 'staff_id' ? <label key={key}>{key === 'hospital_id' ? 'Hospital' : 'Assigned staff (optional)'}<select required={key === 'hospital_id'} value={value === null ? '' : String(value)} onChange={event => {
      const next = event.target.value ? Number(event.target.value) : null
      setBody(current => ({ ...current, [key]: next, ...(key === 'hospital_id' && resource === 'patients' ? { staff_id: null } : {}) }))
    }}>{key === 'staff_id' ? <option value="">Unassigned (null)</option> : <option value="">Select hospital</option>}{data[key === 'hospital_id' ? 'hospitals' : 'staff'].filter(item => key === 'hospital_id' || item.hospital_id === body.hospital_id).map(item => <option value={item.id} key={item.id}>{nameOf(item)} · #{item.id}</option>)}</select></label> : <label key={key}>{key === 'last_check_in' ? 'last check in (UTC)' : key.replaceAll('_', ' ')}<input type={key === 'date_of_birth' || key === 'date_of_admission' ? 'date' : key === 'last_check_in' ? 'datetime-local' : key === 'salary' || key === 'capacity' ? 'number' : 'text'} required={key !== 'description' && key !== 'last_check_in'} min={key === 'salary' || key === 'capacity' ? '0' : undefined} max={key === 'salary' ? '9999999999.99' : key === 'capacity' ? '2147483647' : undefined} step={key === 'salary' ? '0.01' : key === 'last_check_in' ? 'any' : key === 'capacity' ? '1' : undefined} maxLength={key === 'location' || key === 'description' ? 500 : key === 'name' && resource === 'hospitals' ? 200 : 100} value={value === null ? '' : key === 'last_check_in' ? String(value).slice(0, 23) : String(value)} onChange={event => setBody(current => ({ ...current, [key]: (key === 'description' || key === 'last_check_in') && !event.target.value ? null : key === 'capacity' ? Number(event.target.value) : event.target.value }))}/></label>)}
    {resource === 'hospitals' && <p className="muted">Capacity is the maximum patient count. Admissions and transfers into a full hospital are rejected; capacity cannot be lower than its current patient count.</p>}
    {resource === 'roles' && <p className="muted">Access type A, B, or C is a hospital classification stored with this role. It does not enable authentication or restrict this no-login API.</p>}
    {resource === 'staff' && <p className="muted">Admission is a date only. Last check-in is entered in UTC, including date and time; leave blank if there has been no check-in. Salary uses exact decimal currency units with two decimal places.</p>}
    {resource === 'staff' && row && <p>Transferring staff requires unassigning or reassigning their patients first. The API rejects invalid transfers.</p>}
    <h3>Request and SQL preview</h3><Preview requests={[request]}/>
    <div className="modal-actions"><button type="button" className="button secondary" onClick={close}>Cancel</button><button className="button primary" type="submit" disabled={imageBusy || !!imageError}>Review request</button></div>
  </form></Dialog>
}
function ThemeControl({ dark, preference, setPreference }: ReturnType<typeof useTheme>) {
  return <div className="theme-control"><button type="button" className="theme-toggle" role="switch" aria-label="Dark mode" aria-checked={dark} onClick={() => setPreference(dark ? 'light' : 'dark')}><span aria-hidden="true">{dark ? '☾' : '☀'}</span><span>Dark mode</span><span className="theme-track" aria-hidden="true"><span/></span></button><div className="theme-source"><small>{preference === 'system' ? 'Following browser' : 'Saved preference'}</small></div></div>
}
function App() {
  const theme = useTheme()
  const [data, setData] = useState<Database>(emptyDatabase)
  const dataRef = useRef(data)
  const lock = useRef(false)
  const [started, setStarted] = useState(false)
  const [checking, setChecking] = useState(true)
  const [booted, setBooted] = useState(false)
  const bootOnce = useRef(false)
  const [page, setPage] = useState<Page>('Overview')
  function navigate(destination: Page) {
    setPage(destination); setQuery('')
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }
  const [hospital, setHospital] = useState('all')
  const [query, setQuery] = useState('')
  const [review, setReview] = useState<Review | null>(null)
  const [editor, setEditor] = useState<{ resource: Resource; row?: Row } | null>(null)
  const [prerequisite, setPrerequisite] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [logs, setLogs] = useState<Log[]>([])
  const [session, setSession] = useState<TestRun | null>(null)
  const [running, setRunning] = useState(false)
  const [speed, setSpeed] = useState(1)
  const activeTest = !!session && session.index < session.requests.length && !session.failed
  const selected = (rows: Row[]) => hospital === 'all' ? rows : rows.filter(row => row.hospital_id === Number(hospital))
  const patients = selected(data.patients)
  const staff = selected(data.staff)
  const assigned = patients.filter(row => row.staff_id !== null)
  const refs = baselineRefs(data)
  async function execute(request: Request) {
    try {
      const result = await send(request, apiBase)
      dataRef.current = applyResponse(dataRef.current, request, result)
      setData(dataRef.current)
      setLogs(current => [{ request, status: request.resource === 'initialization' ? '200 · OK' : request.method === 'DELETE' ? '204 · saved' : request.method === 'POST' ? '201 · saved' : '200 · OK', detail: request.method === 'GET' && request.id !== undefined ? JSON.stringify(result, null, 2) : undefined }, ...current].slice(0, 100))
      return result
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause)
      setLogs(current => [{ request, status: 'Failed', detail: message }, ...current].slice(0, 100))
      throw cause
    }
  }
  async function refresh() { await runRequests(readRequests(), {}, execute); return dataRef.current }
  async function guarded(action: () => Promise<void>) {
    if (lock.current) return
    lock.current = true; setBusy(true); setError(''); setNotice('')
    try { await action() } catch (cause) { setError(cause instanceof Error ? cause.message : String(cause)); setRunning(false) }
    finally { lock.current = false; setBusy(false) }
  }
  async function bootstrap() {
    setChecking(true); setBooted(false)
    await guarded(async () => {
      const state = await execute(initializationRequest())
      if (!isInitialization(state)) throw new Error('Invalid initialization response. Rebuild the backend and refresh.')
      await refresh()
      setStarted(state.was_initialized); setBooted(true)
    })
    setChecking(false)
  }
  useEffect(() => {
    if (bootOnce.current) return
    bootOnce.current = true
    void bootstrap()
    // One database-backed startup check per mount, including React Strict Mode.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  function showPopulation(snapshot = dataRef.current, thenTest = false) {
    const plan = populationPlan(snapshot)
    const expected = fingerprint(snapshot)
    setReview({ title: 'Populate demo data', description: 'Restore the fixed baseline: 2 demo hospitals, 3 roles, 3 staff, and 4 patients. All patients and staff inside the two reserved [Demo] hospitals will be deleted and recreated. Their IDs may change. Other hospitals and their records are preserved. This writes to the real database.', requests: [...plan, initializationRequest(true)], reads: [...readRequests(), ...readRequests()], writesOnly: true, confirm: 'Populate database', action: async () => {
      await refresh()
      if (fingerprint(dataRef.current) !== expected) {
        showPopulation(dataRef.current, thenTest)
        setNotice('Records changed since the preview. No population writes were sent; review the updated plan before confirming again.')
        return
      }
      await runRequests(plan, {}, execute)
      await refresh()
      if (!baselineRefs(dataRef.current)) throw new Error(`Population verification failed: ${baselineProblems(dataRef.current).join('; ')}`)
      await execute(initializationRequest(true))
      setStarted(true); setSession(null); setRunning(false); setPage(thenTest ? 'Testing' : 'Overview'); setHospital('all')
      setNotice('Demo baseline saved to MySQL: 2 hospitals, 3 roles, 3 staff, 4 patients.')
      if (thenTest) showTest(dataRef.current)
    } })
  }
  function showTest(snapshot = dataRef.current) {
    const ids = baselineRefs(snapshot)
    if (!ids) { setPrerequisite(true); return }
    const plan = testPlan().map(request => resolveRequest(request, ids))
    const expected = fingerprint(snapshot)
    setReview({ title: 'Run the predetermined test', description: 'Simulate 08:00–15:00 in eight ordered steps. Admit two patients, assign Jamie, transfer Casey with a clinician, discharge Sam by deleting the record, unassign Alex, add Mia’s coordinator role, and update Riverside’s location. Final demo state: 2 hospitals, 3 roles, 3 staff, 5 patients (4 assigned, 1 unassigned). Each step commits separately. Completed changes remain in MySQL if paused, stopped, or interrupted.', requests: [...readRequests(), ...plan, ...readRequests()], confirm: 'Run test on dashboard', action: async () => {
      await refresh()
      if (fingerprint(dataRef.current) !== expected || !baselineRefs(dataRef.current)) throw new Error('The database changed since this preview. No test writes were sent. Review the test again; Populate may be required.')
      setSession({ requests: plan, refs: ids, index: 0 }); setRunning(true); setPage('Overview'); setHospital('all')
    } })
  }
  async function nextStep() {
    if (!session || !activeTest || lock.current) return
    await guarded(async () => {
      let committed = session.index
      try {
        await execute(session.requests[session.index])
        committed += 1
        const next = session.index + 1
        setSession({ ...session, index: next })
        if (next === session.requests.length) {
          setRunning(false)
          await refresh()
          if (!finalStateMatches(dataRef.current, session.refs)) throw new Error('All steps were sent, but final verification did not match. Inspect the database and request log before rerunning.')
          setNotice('Test complete. The persisted final demo state was verified through the API.')
        }
      } catch (cause) { setSession({ ...session, index: committed, failed: true }); throw cause }
    })
  }
  useEffect(() => {
    if (!running || busy || !activeTest) return
    const id = window.setTimeout(() => { void nextStep() }, 3000 / speed)
    return () => window.clearTimeout(id)
    // Schedule one committed request at a time; no interval can overlap a write.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running, busy, session, speed, activeTest])
  function start(populate: boolean) {
    if (populate) { showPopulation(); return }
    setReview({ title: 'Start without demo data', description: 'Keep the current domain records and remember this startup choice in MySQL. On refresh or in another browser, the dashboard opens directly. No demo records are created or deleted.', requests: [initializationRequest(true)], confirm: 'Start dashboard', action: async () => {
      await execute(initializationRequest(true)); setStarted(true)
    } })
  }
  function manual(request: Request) {
    setEditor(null)
    setReview({ title: request.title, description: request.method === 'DELETE' ? 'Delete this record from MySQL. Deletion is permanent; referenced records may be protected by the API. The collections will then reload.' : request.method === 'GET' ? 'Read this record from the API. Its JSON response appears in the request log.' : 'Save these values through the API, then reload all collections from MySQL.', requests: request.method === 'GET' ? [request] : [request, ...readRequests()], confirm: request.method === 'GET' ? 'Read record' : 'Send request', action: async () => {
      await execute(request)
      if (request.method !== 'GET') await refresh()
      setNotice(request.method === 'GET' ? 'Record read. Open the request log to inspect its JSON response.' : 'Database updated and records reloaded.')
    } })
  }
  const modal = <>
    {review && <Dialog title={review.title} close={() => { if (!busy) setReview(null) }}><p>{review.description}</p><p className="muted">{review.writesOnly ? 'The main preview shows the records to insert, update, or delete, in order. Validation and verification reads are listed separately below.' : 'Requests run in the order below.'} Named ID placeholders refer to IDs returned by earlier API responses.</p>{review.writesOnly && <h3>Planned database writes</h3>}<Preview requests={review.requests} expanded={review.writesOnly} writesOnly={review.writesOnly}/>{review.reads && <details><summary>Supporting reads: preflight and final verification</summary><Preview requests={review.reads}/></details>}<div className="modal-actions"><button className="button secondary" disabled={busy} onClick={() => setReview(null)}>Cancel</button><button className="button primary" disabled={busy} onClick={() => { const action = review.action; setReview(null); void guarded(action) }}>{review.confirm}</button></div></Dialog>}
    {prerequisite && <Dialog title="Populate the baseline first" close={() => setPrerequisite(false)}><p>The test needs the exact predefined demo records and assignments. They are missing, were edited, or a previous test changed them. Populate restores the baseline before another test can run.</p><p>You will review every reset and creation request before it is sent. After population, the test preview opens for a separate confirmation.</p><div className="modal-actions"><button className="button secondary" onClick={() => setPrerequisite(false)}>Cancel</button><button className="button primary" onClick={() => { setPrerequisite(false); showPopulation(dataRef.current, true) }}>Review Populate</button></div></Dialog>}
    {editor && <Editor {...editor} data={data} close={() => setEditor(null)} save={manual}/>}
  </>
  const messages = <>{error && <div className="alert error" role="alert">{error} Changes already confirmed by the API are retained. Refresh before retrying; requests are never retried automatically.</div>}{notice && <div className="alert success" role="status">{notice}</div>}{busy && <div className="alert" role="status">Waiting for the API…</div>}</>
  if (checking || !booted) return <div className="welcome"><div className="welcome-body"><h1>HospitalSim</h1><p>Checking the database initialization flag and loading API records. These reads do not create demo data.</p>{messages}{!checking && <button className="button primary" disabled={busy} onClick={() => { void bootstrap() }}>Retry connection</button>}<details><summary>Startup reads and illustrative SQL</summary><Preview requests={[initializationRequest(), ...readRequests()]}/></details></div></div>
  if (!started) return <div className="welcome"><div className="welcome-header"><span className="brand-mark">+</span><strong>HospitalSim</strong><a href="https://marcelopenas.github.io/HospitalSim/" target="_blank" rel="noreferrer">Documentation ↗</a><a href={swaggerUrl} target="_blank" rel="noreferrer">Swagger API ↗</a><ThemeControl {...theme}/></div><div className="welcome-body"><div className="eyebrow">HOSPITAL OPERATIONS</div><h1>How would you like to begin?</h1><p>This choice appears once per database. After you start empty or successfully populate, MySQL remembers the choice across refreshes and browsers.</p>{messages}<div className="welcome-options"><section className="panel"><Icon name="hospital" size={34}/><h2>Start empty</h2><p>Build your own hospitals, roles, staff, and patient records manually. Existing database records, if any, are kept.</p><button className="button secondary" disabled={busy} onClick={() => start(false)}>Start without adding demo data</button></section><section className="panel"><Icon name="pulse" size={34}/><h2>Pre-populate</h2><p>Review and create a fixed demo dataset, then run a predetermined sequence of real API operations in Testing.</p><button className="button primary" disabled={busy} onClick={() => start(true)}>Review demo population</button></section></div><details><summary>Startup reads and illustrative SQL</summary><Preview requests={[initializationRequest(), ...readRequests()]}/></details></div>{modal}</div>
  const rows = page === 'patients' ? selected(data.patients) : page === 'staff' ? selected(data.staff) : page === 'hospitals' ? data.hospitals.filter(row => hospital === 'all' || row.id === Number(hospital)) : page === 'roles' ? data.roles : []
  const filtered = rows.filter(row => JSON.stringify(Object.fromEntries(Object.entries(row).filter(([key]) => key !== 'image_blob'))).toLowerCase().includes(query.toLowerCase()))
  function Table({ resource, records, editable = true }: { resource: Resource; records: Row[]; editable?: boolean }) {
    const columns = resource === 'hospitals' ? ['name', 'location', 'capacity'] : resource === 'roles' ? ['name', 'description', 'access_type'] : resource === 'staff' ? ['first_name', 'last_name', 'date_of_admission', 'last_check_in', 'salary', 'hospital_id', 'role_ids'] : ['image_blob', 'first_name', 'last_name', 'date_of_birth', 'hospital_id', 'staff_id']
    const display = (key: string, row: Row): ReactNode => key === 'image_blob' ? <img className="patient-avatar" src={avatarSource(row.image_blob)} alt={`${nameOf(row)} profile`}/> : key === 'last_check_in' ? row[key] ? String(row[key]).replace('T', ' ') + ' UTC' : '—' : key === 'hospital_id' ? nameOf(data.hospitals.find(h => h.id === row[key])) : key === 'staff_id' ? nameOf(data.staff.find(s => s.id === row[key])) : key === 'role_ids' ? (row[key] as number[]).map(id => nameOf(data.roles.find(r => r.id === id))).join(', ') || 'No roles' : row[key] === null ? '—' : String(row[key])
    return <div className="table-scroll"><table><thead><tr><th>ID</th>{columns.map(key => <th key={key}>{key === 'image_blob' ? 'profile' : key.replaceAll('_', ' ')}</th>)}{editable && <th>Actions</th>}</tr></thead><tbody>{records.map(row => <tr key={row.id}><td>#{row.id}</td>{columns.map(key => <td key={key}>{display(key, row)}</td>)}{editable && <td><div className="row-actions"><button className="text-button" disabled={busy || activeTest} onClick={() => manual({ method: 'GET', resource, id: row.id, title: `Read ${resource} #${row.id}` })}>Read</button><button className="text-button" disabled={busy || activeTest} onClick={() => setEditor({ resource, row })}>Edit</button><button className="text-button danger" disabled={busy || activeTest} onClick={() => manual({ method: 'DELETE', resource, id: row.id, title: `Delete ${resource} #${row.id}` })}>Delete</button></div></td>}</tr>)}</tbody></table>{!records.length && <div className="empty">No records. Create entries manually or use Populate in Testing.</div>}</div>
  }
  const title = page === 'Overview' ? 'A pulse on your hospital.' : page === 'Testing' ? 'Predictable steps. Real changes.' : `${labels[page]} directory`
  return <div className="app-shell"><a className="skip-link" href="#main">Skip to content</a><aside className="sidebar"><button className="brand brand-button" onClick={() => navigate('Overview')}><span className="brand-mark">+</span><span>Hospital<span className="brand-light">Sim</span><small>OPERATIONS DASHBOARD</small></span></button><div className="nav-label">WORKSPACE</div><nav aria-label="Main navigation">{(['Overview', 'patients', 'staff', 'roles', 'hospitals', 'Testing'] as Page[]).map(item => <button key={item} className={`nav-item ${page === item ? 'selected' : ''}`} aria-current={page === item ? 'page' : undefined} onClick={() => navigate(item)}><Icon name={item === 'Overview' ? 'grid' : item === 'patients' ? 'heart' : item === 'hospitals' ? 'hospital' : item === 'Testing' ? 'play' : 'users'}/>{item === 'Overview' || item === 'Testing' ? item : labels[item]}</button>)}</nav><div className="sidebar-bottom"><section className="sidebar-note" aria-label="API connection"><Icon name="pulse"/><h3>Connected to your API.</h3><p>Manual operations and deterministic tests use the same CRUD endpoints.</p><div className="connection-status"><span><span className="status-dot"/>MySQL through FastAPI</span><small>No login required</small></div></section><div className="sidebar-profile" aria-label="Local profile"><div className="profile-identity"><span className="profile-avatar"><Icon name="users" size={18}/></span><div><strong>Local workspace</strong><small>No login required</small></div></div><ThemeControl {...theme}/></div></div></aside>
    <div className="workspace"><header className="topbar"><div className="breadcrumb">Workspace <Icon name="chevron" size={13}/><strong>{page === 'Overview' || page === 'Testing' ? page : labels[page]}</strong></div><div className="top-links"><a href="https://marcelopenas.github.io/HospitalSim/" target="_blank" rel="noreferrer"><Icon name="book" size={17}/>Documentation ↗</a><a href={swaggerUrl} target="_blank" rel="noreferrer"><Icon name="code" size={17}/>Swagger API ↗</a><span className="demo-pill">API CONNECTED</span></div></header>
    <main id="main"><div className="page-heading"><div><div className="eyebrow"><span className="status-dot"/> HOSPITAL OPERATIONS</div><h1>{title}</h1><p>Records and assignments from MySQL. Changes are sent through the API.</p></div><label className="hospital-select"><span className="sr-only">Select hospital</span><select aria-label="Select hospital" value={hospital} onChange={event => setHospital(event.target.value)}><option value="all">All hospitals</option>{data.hospitals.map(row => <option value={row.id} key={row.id}>{nameOf(row)}</option>)}</select></label></div>
    {messages}
    {session && <section className="simulation-bar" aria-label="Test controls"><div className="simulation-state"><span className="sim-indicator"><Icon name="pulse"/></span><div><strong>{session.failed ? 'Test stopped after an error' : activeTest ? running ? 'Test running' : 'Test paused' : 'Test completed'}</strong><small>{session.index} / {session.requests.length} operations committed · {session.requests[Math.min(session.index, session.requests.length - 1)].hour}:00</small></div></div><div className="sim-controls"><select aria-label="Test speed" value={speed} onChange={event => setSpeed(Number(event.target.value))}><option value={1}>1× speed</option><option value={2}>2× speed</option><option value={4}>4× speed</option></select><button className="button secondary" disabled={busy || !activeTest} onClick={() => { setRunning(false); void nextStep() }}>Next hour</button><button className="button primary" disabled={!activeTest} onClick={() => setRunning(!running)}>{running ? 'Pause after request' : 'Resume'}</button><button className="button secondary" disabled={busy} onClick={() => { setRunning(false); setSession(null); setPage('Testing') }}>End session</button></div></section>}
    {page === 'Overview' && <><section className="metrics" aria-label="Database metrics">{[
      { label: 'Patient records', value: patients.length, icon: 'heart', detail: 'Current patient registry', color: 'teal' },
      { label: 'Assigned to care', value: assigned.length, icon: 'check', detail: `${patients.length - assigned.length} without an assigned clinician`, color: 'blue' },
      { label: 'Staff members', value: staff.length, icon: 'users', detail: `${data.roles.length} roles across the database`, color: 'purple' },
      { label: 'Hospitals', value: hospital === 'all' ? data.hospitals.length : data.hospitals.filter(row => row.id === Number(hospital)).length, icon: 'hospital', detail: `${data.hospitals.filter(row => hospital === 'all' || row.id === Number(hospital)).reduce((total, row) => total + Number(row.capacity), 0)} total patient capacity`, color: 'amber' },
    ].map(metric => <article className="metric-card" key={metric.label}><div className="metric-label">{metric.label}<span className={`metric-icon ${metric.color}`}><Icon name={metric.icon}/></span></div><div className="metric-value">{metric.value}</div><div className="metric-detail">{metric.detail}</div></article>)}</section><div className="charts-grid"><section className="panel"><div className="panel-header"><div><h2>Care assignments</h2><p>Patient records grouped by assigned staff</p></div></div><div className="ward-list">{staff.map(row => { const count = patients.filter(p => p.staff_id === row.id).length; return <div key={row.id}><div className="ward-label"><strong>{nameOf(row)}</strong><span>{count} patient{count === 1 ? '' : 's'}</span></div><div className="track"><div style={{ width: `${patients.length ? count / patients.length * 100 : 0}%` }}/></div></div> })}{!staff.length && <p className="muted">Create a hospital and staff, or pre-populate from Testing.</p>}</div></section><section className="panel briefing"><h2>Testing workspace</h2><p>Populate a fixed baseline, inspect the HTTP and SQL previews, then run eight predetermined operations against MySQL.</p><button className="button primary" onClick={() => setPage('Testing')}>Open Testing →</button><p className="muted">Counts reflect the last successful API responses. Use Refresh below to load changes made by other clients.</p></section></div><section className="panel"><div className="panel-header"><div><h2>Patient registry</h2><p>Current records returned by the API</p></div><button className="text-button" onClick={() => setPage('patients')}>Manage patients →</button></div><Table resource="patients" records={patients.slice(-5)} editable={false}/></section></>}
    {page !== 'Overview' && page !== 'Testing' && <section className="panel"><div className="panel-header"><div><h2>{labels[page]} <span className="count-tag">{filtered.length}</span></h2><p>Create, read, update, and delete real records.</p></div><button className="button primary" disabled={busy || activeTest || ((page === 'staff' || page === 'patients') && !data.hospitals.length)} onClick={() => setEditor({ resource: page })}>+ Create record</button></div><div className="table-toolbar"><label className="search"><Icon name="search" size={17}/><input aria-label="Search records" placeholder="Search the loaded records…" value={query} onChange={event => setQuery(event.target.value)}/></label>{(page === 'staff' || page === 'patients') && !data.hospitals.length && <p className="muted">Create a hospital first.</p>}{activeTest && <p className="muted">End the test session before editing records manually.</p>}</div><Table resource={page} records={filtered}/></section>}
    {page === 'Testing' && <><div className="testing-actions"><section className="panel briefing"><span className="badge teal">1 · BASELINE</span><h2>Populate</h2><p>Create or restore 2 demo hospitals, 3 roles, 3 staff, and 4 patients with fixed names, dates, and assignments.</p><p>The two reserved [Demo] hospitals are reset. Their patient and staff records are recreated; unrelated hospitals are preserved.</p><button className="button secondary" disabled={busy || activeTest} onClick={() => showPopulation()}>Populate</button></section><section className="panel briefing"><span className="badge blue">2 · PREDETERMINED OPERATIONS</span><h2>Test</h2><p>Run the same eight hourly operations every time. The final demo dataset has 5 patients: 4 assigned and 1 unassigned.</p><p>{refs ? 'The loaded data matches the required baseline.' : 'Populate is required: the loaded data does not match the baseline.'} The API checks are repeated before execution.</p><button className="button primary" disabled={busy || activeTest} onClick={() => showTest()}>Test</button></section></div><section className="panel briefing"><h2>What will happen?</h2><p>08:00–15:00: two admissions, one clinician assignment, one hospital transfer, one discharge (DELETE), one unassignment, one added staff role, and one hospital location update. Actual server IDs are resolved from Populate responses. Auto-increment IDs can differ between runs; the resulting demo values and relationships are fixed.</p><p>Each request is committed independently. Pause waits for any in-flight request to finish. End session leaves completed changes in the database. A failed request stops the sequence, without retrying or rolling back earlier steps. Populate restores the starting state for another run.</p><h3>Requests and database changes</h3><Preview requests={testPlan().map(request => refs ? resolveRequest(request, refs) : request)}/></section></>}
    <section className="panel briefing connection"><div className="connection-heading"><h2>API reads and request log</h2><button className="button secondary" disabled={busy || activeTest} onClick={() => setReview({ title: 'Refresh API records', description: 'Read all four collections from MySQL. No database changes are made.', requests: readRequests(), confirm: 'Refresh records', action: async () => { await refresh(); setNotice('Records refreshed from the API.') } })}>Refresh records</button></div><p>API endpoint: <code>{apiBase}</code>. Search and hospital filters operate on these loaded records and send no requests.</p><details><summary>Refresh request and SQL previews</summary><Preview requests={readRequests()}/></details><SqlNote/><div className="request-log">{logs.slice(0, 30).map((entry, index) => <details key={index}><summary><span className={entry.status === 'Failed' ? 'danger' : ''}>{entry.status}</span> · {entry.request.method} {pathOf(entry.request)} · {entry.request.title}</summary>{entry.detail && <pre>{entry.detail}</pre>}<Preview requests={[entry.request]} expanded/></details>)}</div></section>
    <footer className="page-footer"><span>HospitalSim · FastAPI + MySQL</span><span>Demo SQL is illustrative. The browser sends HTTP and JSON.</span></footer></main></div>{modal}</div>
}
export default App
