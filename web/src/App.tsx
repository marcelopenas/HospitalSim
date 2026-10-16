import { useEffect, useRef, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { admit, advanceHour, capacity, clinicians, clock, day, discharge, hospitals, initialSimulation, occupied, step, wardCount, wards } from './simulation'
import type { Scenario, Simulation, WardName } from './simulation'
import './App.css'

type Page = 'Overview' | 'Patients' | 'Staff & roles' | 'Hospitals'
const storageKey = 'hospitalsim.demo.v1'
function load(): Simulation[] {
  try {
    const data = JSON.parse(localStorage.getItem(storageKey) ?? 'null')
    if (Array.isArray(data) && data.length === hospitals.length && data.every((s, i) => s.version === 1 && s.hospital === i && Number.isFinite(s.minute) && Array.isArray(s.patients) && Array.isArray(s.history) && Array.isArray(s.events) && Number.isFinite(s.seed) && Number.isFinite(s.nextId))) return data
  } catch { /* A fresh demo also works when browser storage is unavailable. */ }
  return hospitals.map((_, i) => initialSimulation(i))
}
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
const pages: { name: Page; icon: string }[] = [{ name: 'Overview', icon: 'grid' }, { name: 'Patients', icon: 'heart' }, { name: 'Staff & roles', icon: 'users' }, { name: 'Hospitals', icon: 'hospital' }]
function App() {
  const [simulations, setSimulations] = useState(load)
  const [hospital, setHospital] = useState(0)
  const [page, setPage] = useState<Page>('Overview')
  const [running, setRunning] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [scenario, setScenario] = useState<Scenario>('normal')
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('Active')
  const [modal, setModal] = useState<'admit' | 'reset' | null>(null)
  const [notice, setNotice] = useState('')
  const [storageWarning, setStorageWarning] = useState(false)
  const dialogRef = useRef<HTMLDialogElement>(null)
  const s = simulations[hospital]
  const h = hospitals[hospital]
  const beds = capacity(hospital)
  const inCare = occupied(s)
  const waiting = s.patients.filter(p => p.status === 'Waiting').length
  const occupancy = Math.round(inCare / beds * 100)
  const active = s.patients.filter(p => p.status !== 'Discharged')
  const swaggerUrl = import.meta.env.VITE_SWAGGER_URL || `http://${window.location.hostname}:8080/docs`
  const update = (fn: (s: Simulation) => Simulation) => setSimulations(all => all.map((item, i) => i === hospital ? fn(item) : item))
  useEffect(() => {
    try { localStorage.setItem(storageKey, JSON.stringify(simulations)) } catch { setStorageWarning(true) }
  }, [simulations])
  useEffect(() => {
    if (!running) return
    const id = window.setInterval(() => {
      setSimulations(all => all.map((item, i) => i === hospital ? step(item, scenario) : item))
    }, 3000 / speed)
    return () => window.clearInterval(id)
  }, [running, speed, hospital, scenario])
  useEffect(() => {
    if (modal) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [modal])
  useEffect(() => { if (!notice) return; const id = window.setTimeout(() => setNotice(''), 4000); return () => window.clearTimeout(id) }, [notice])
  function submitPatient(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const name = String(data.get('name')).trim()
    if (!name) return
    update(current => admit(current, name, Number(data.get('age')), data.get('ward') as WardName))
    setModal(null); setNotice(`${name} added to the simulation.`)
  }
  const matched = [...s.patients].reverse().filter(p => (filter === 'All' || (filter === 'Active' ? p.status !== 'Discharged' : p.status === filter)) && `${p.name} ${p.id} ${p.ward} ${p.clinician}`.toLowerCase().includes(query.toLowerCase()))
  function PatientTable({ compact = false }: { compact?: boolean }) {
    const rows = compact ? [...active].reverse().slice(0, 5) : matched
    return <div className="table-scroll"><table><thead><tr><th>Patient</th><th>Department</th><th>Assigned clinician</th><th>Status</th><th>{compact ? 'Arrival' : 'Action'}</th></tr></thead><tbody>{rows.map(p => <tr key={p.id}><td><div className="person"><span className="avatar">{p.name.split(' ').map(n => n[0]).slice(0, 2).join('')}</span><div><strong>{p.name}</strong><small>PT-{p.id} <span>·</span> {p.age} years</small></div></div></td><td>{p.ward}</td><td>{p.clinician}</td><td><span className={`badge ${p.status === 'Waiting' ? 'amber' : p.status === 'Discharged' ? 'gray' : 'teal'}`}><i/>{p.status}</span></td><td>{compact ? clock(p.admitted) : p.status === 'In care' ? <button className="text-button" onClick={() => { update(current => discharge(current, p.id)); setNotice(`${p.name} discharged.`) }}>Discharge <span aria-hidden="true">→</span></button> : '—'}</td></tr>)}</tbody></table>{!rows.length && <div className="empty">No patients match this view. Try a different search or admit a patient.</div>}</div>
  }
  return <div className="app-shell">
    <a className="skip-link" href="#main">Skip to content</a>
    <aside className="sidebar">
      <a className="brand" href="#overview" onClick={() => setPage('Overview')}><span className="brand-mark">+</span><span>Hospital<span className="brand-light">Sim</span><small>OPERATIONS SANDBOX</small></span></a>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Main navigation">{pages.map(item => <button key={item.name} className={`nav-item ${page === item.name ? 'selected' : ''}`} aria-current={page === item.name ? 'page' : undefined} onClick={() => { setPage(item.name); setQuery('') }}><Icon name={item.icon}/>{item.name}{item.name === 'Patients' && <span className="nav-count">{active.length}</span>}</button>)}</nav>
      <div className="sidebar-note"><span className="note-icon"><Icon name="pulse"/></span><h3>A little practice.<br/>A clearer picture.</h3><p>Explore how patient flow and hospital capacity work together.</p><a href="https://marcelopenas.github.io/HospitalSim/" target="_blank" rel="noreferrer">Explore the documentation <Icon name="arrow" size={14}/></a></div>
      <div className="sidebar-footer"><span className="status-dot"/> Demo environment<small>Synthetic data · No login required</small></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="breadcrumb">Workspace <Icon name="chevron" size={13}/><strong>{page}</strong></div><div className="top-links"><a href="https://marcelopenas.github.io/HospitalSim/" target="_blank" rel="noreferrer"><Icon name="book" size={17}/>Documentation <Icon name="arrow" size={13}/></a><a href={swaggerUrl} target="_blank" rel="noreferrer"><Icon name="code" size={17}/>Swagger API <Icon name="arrow" size={13}/></a><span className="demo-pill">DEMO</span></div></header>
      <main id="main">
        <div className="page-heading"><div><div className="eyebrow"><span className="status-dot"/> HOSPITAL OPERATIONS</div><h1>{page === 'Overview' ? 'A pulse on your hospital.' : page === 'Patients' ? 'Every patient, in view.' : page === 'Staff & roles' ? 'The people behind the care.' : 'Your hospital network.'}</h1><p>{page === 'Overview' ? 'Explore patient flow, care teams, and capacity in one place.' : page === 'Patients' ? 'Follow admissions, bed assignments, and discharges in your demo.' : page === 'Staff & roles' ? 'Understand care assignments and staffing across departments.' : 'Two fictional hospitals. One place to explore their operations.'}</p></div><label className="hospital-select"><Icon name="hospital"/><span className="sr-only">Select hospital</span><select aria-label="Select hospital" value={hospital} onChange={e => { setHospital(Number(e.target.value)); setRunning(false) }}>{hospitals.map((item, i) => <option key={item.name} value={i}>{item.name}</option>)}</select></label></div>
        <section className="simulation-bar" aria-label="Simulation controls"><div className="simulation-state"><span className={`sim-indicator ${running ? 'running' : ''}`}><Icon name="pulse" size={19}/></span><div><strong>Simulation {running ? 'running' : 'ready'}</strong><small>Browser-only demo · Changes stay on this device</small></div></div><div className="sim-controls"><label><span className="sr-only">Scenario</span><select aria-label="Scenario" value={scenario} onChange={e => setScenario(e.target.value as Scenario)}><option value="normal">Normal operations</option><option value="surge">Patient surge</option><option value="critical">Critical demand</option></select></label><span className="sim-time"><Icon name="clock" size={15}/> Day {day(s.minute)} · {clock(s.minute)}</span><select aria-label="Simulation speed" value={speed} onChange={e => setSpeed(Number(e.target.value))}><option value={1}>1× speed</option><option value={2}>2× speed</option><option value={4}>4× speed</option></select><button className="icon-button" aria-label="Reset simulation" title="Reset simulation" onClick={() => { setRunning(false); setModal('reset') }}><Icon name="reset" size={18}/></button><button className="button secondary" onClick={() => update(current => advanceHour(current, scenario))}>+1 hour</button><button className="button primary" onClick={() => setRunning(!running)}><Icon name={running ? 'pause' : 'play'} size={15}/>{running ? 'Pause' : 'Run simulation'}</button></div></section>
        {storageWarning && <div className="alert" role="status">Browser storage is unavailable. Your demo works for this visit, but changes may not survive a refresh.</div>}
        {waiting > 0 && <div className="alert" role="status"><strong>{waiting} patient{waiting === 1 ? '' : 's'} waiting for a bed.</strong> {beds - inCare} beds available across the hospital; assignments depend on department capacity.</div>}
        {page === 'Overview' && <>
          <section className="metrics" aria-label="Hospital metrics">{[
            { label: 'Active patients', value: active.length, icon: 'heart', detail: `${s.arrivals} admissions this simulation`, color: 'teal' },
            { label: 'Bed occupancy', value: `${occupancy}%`, icon: 'bed', detail: `${inCare} occupied · ${beds - inCare} available`, color: 'blue' },
            { label: 'Staff on duty', value: h.staff, icon: 'users', detail: `4 care teams across ${wards.length} departments`, color: 'purple' },
            { label: 'Waiting for care', value: waiting, icon: 'clock', detail: waiting ? 'Department capacity reached' : 'All patients have a bed', color: 'amber' },
          ].map(m => <article className="metric-card" key={m.label}><div className="metric-label">{m.label}<span className={`metric-icon ${m.color}`}><Icon name={m.icon}/></span></div><div className="metric-value">{m.value}</div><div className="metric-detail">{m.icon === 'clock' && !waiting && <Icon name="check" size={13}/>} {m.detail}</div></article>)}</section>
          <div className="charts-grid"><section className="panel flow-panel"><div className="panel-header"><div><h2>Patient flow</h2><p>Cumulative admissions and discharges since the start</p></div><span className="soft-label">{s.history.length > 1 ? 'Last 6 hours' : 'Awaiting first step'}</span></div><FlowChart simulation={s}/></section><section className="panel"><div className="panel-header"><div><h2>Department capacity</h2><p>Occupied beds by care unit</p></div><span className="plain-icon"><Icon name="bed" size={18}/></span></div><div className="ward-list">{wards.map((ward, i) => { const count = wardCount(s, ward); const pct = count / h.capacities[i] * 100; return <div key={ward}><div className="ward-label"><strong>{ward}</strong><span><b>{count}</b> / {h.capacities[i]}</span></div><div className="track"><div className={pct >= 90 ? 'high' : ''} style={{ width: `${pct}%` }}/></div></div> })}<div className="capacity-legend"><span><i/> Available capacity</span><span><i className="amber-dot"/> ≥90% occupied</span></div></div></section></div>
          <div className="bottom-grid"><section className="panel patient-panel"><div className="panel-header"><div><h2>Patients in the hospital <span className="count-tag">{active.length}</span></h2><p>The latest arrivals in your simulation</p></div><button className="text-button" onClick={() => setPage('Patients')}>View all patients →</button></div><PatientTable compact/></section><section className="panel activity-panel"><div className="panel-header"><div><h2>Activity feed</h2><p>What’s happening on the floor</p></div><span className={`live-label ${running ? 'is-live' : ''}`}><i/>{running ? 'LIVE' : 'PAUSED'}</span></div><div className="activity-list">{s.events.slice(0, 4).map(e => <div className="activity" key={e.id}><span className={`event-icon ${e.type}`}><Icon name={e.type === 'arrival' ? 'plus' : e.type === 'discharge' ? 'check' : 'pulse'} size={15}/></span><div><p>{e.text}</p><small>Day {day(e.minute)} · {clock(e.minute)}</small></div></div>)}</div></section></div>
        </>}
        {page === 'Patients' && <section className="panel"><div className="panel-header"><div><h2>Patient directory <span className="count-tag">{matched.length}</span></h2><p>Synthetic records for {h.name}</p></div><button className="button primary" onClick={() => setModal('admit')}><Icon name="plus" size={16}/>Admit patient</button></div><div className="table-toolbar"><label className="search"><Icon name="search" size={17}/><input aria-label="Search patients" placeholder="Search name, ID, department…" value={query} onChange={e => setQuery(e.target.value)}/></label><select aria-label="Filter patients" value={filter} onChange={e => setFilter(e.target.value)}>{['Active', 'All', 'In care', 'Waiting', 'Discharged'].map(f => <option key={f}>{f}</option>)}</select><span className="muted">{s.discharges} discharges this simulation</span></div><PatientTable/></section>}
        {page === 'Staff & roles' && <><div className="section-intro"><h2>Care team directory</h2><p>8 named clinicians represent {h.staff} simulated staff on duty. Patient assignments are made to the lead clinician in each department.</p></div><section className="staff-grid">{clinicians.map((person, i) => { const load = s.patients.filter(p => p.status === 'In care' && p.clinician === person.name).length; return <article className="panel staff-card" key={person.name}><span className={`staff-avatar color-${i % 4}`}>{person.name.replace('Dr. ', '').split(' ').map(n => n[0]).join('')}</span><h2>{person.name}</h2><span className="badge teal">{person.role}</span><p>{person.ward}</p><div className="staff-load"><span>Assigned patients</span><strong>{load}</strong></div></article> })}</section></>}
        {page === 'Hospitals' && <section className="hospital-grid">{hospitals.map((item, i) => <article className="panel hospital-card" key={item.name}><div className="hospital-card-top"><span className="metric-icon teal"><Icon name="hospital" size={25}/></span><span className="badge gray">Fictional hospital</span></div><h2>{item.name}</h2><p>{item.location}</p><div className="hospital-stats"><div><strong>{capacity(i)}</strong><span>Total beds</span></div><div><strong>{occupied(simulations[i])}</strong><span>Occupied</span></div><div><strong>{item.staff}</strong><span>Staff on duty</span></div></div><button className={`button ${i === hospital ? 'secondary' : 'primary'}`} onClick={() => { setHospital(i); setRunning(false); setPage('Overview') }}>Open dashboard <span aria-hidden="true">→</span></button></article>)}</section>}
        <footer className="page-footer"><span><Icon name="pulse" size={14}/> Built to explore. Designed to learn.</span><span>HospitalSim <span className="footer-dot">·</span> Synthetic data only</span></footer>
      </main>
    </div>
    <div className="toast-region" role="status" aria-live="polite">{notice && <div className="toast"><Icon name="check" size={17}/>{notice}</div>}</div>
    <dialog ref={dialogRef} onCancel={() => setModal(null)} onClose={() => setModal(null)}>
      {modal === 'admit' ? <form onSubmit={submitPatient}><div className="modal-heading"><h2>Admit a demo patient</h2><button type="button" className="icon-button" aria-label="Close dialog" onClick={() => setModal(null)}>×</button></div><p>This creates a synthetic record in your browser simulation.</p><label>Patient name<input name="name" required maxLength={100} pattern=".*\S.*" autoFocus placeholder="e.g. Alex Taylor"/></label><label>Age<input name="age" type="number" min="0" max="120" required defaultValue={35}/></label><label>Department<select name="ward">{wards.map(w => <option key={w}>{w}</option>)}</select></label><p className="muted">A lead clinician is assigned automatically. If the department is full, the patient joins its waiting queue.</p><div className="modal-actions"><button type="button" className="button secondary" onClick={() => setModal(null)}>Cancel</button><button className="button primary" type="submit">Admit patient</button></div></form> : <div><h2>Reset this hospital?</h2><p>This clears the simulated activity for {h.name} and restores its initial day shift. The other hospital keeps its progress.</p><div className="modal-actions"><button className="button secondary" onClick={() => setModal(null)}>Keep progress</button><button className="button primary" onClick={() => { update(() => initialSimulation(hospital)); setModal(null); setNotice('Hospital simulation reset to Day 1, 08:00.') }}>Reset simulation</button></div></div>}
    </dialog>
  </div>
}
function FlowChart({ simulation: s }: { simulation: Simulation }) {
  const max = Math.max(10, ...s.history.map(p => Math.max(p.arrivals, p.discharges)))
  const top = Math.ceil(max / 10) * 10
  const x = (i: number) => 42 + i / Math.max(1, s.history.length - 1) * 548
  const y = (value: number) => 170 - value / top * 140
  const line = (key: 'arrivals' | 'discharges') => s.history.map((p, i) => `${x(i)},${y(p[key])}`).join(' ')
  return <div className="flow-chart"><div className="chart-legend"><span><i/>Admissions <b>{s.arrivals}</b></span><span><i className="discharge-dot"/>Discharges <b>{s.discharges}</b></span></div><svg viewBox="0 0 620 215" role="img" aria-label={`Patient flow: ${s.arrivals} admissions and ${s.discharges} discharges since the simulation started.`}><defs><linearGradient id="flow-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#148b78" stopOpacity=".17"/><stop offset="100%" stopColor="#148b78" stopOpacity=".01"/></linearGradient></defs>{[0, 1, 2, 3, 4].map(i => <g key={i}><line x1="42" x2="590" y1={30 + i * 35} y2={30 + i * 35} stroke="#edf0f2" strokeDasharray="4 4"/><text x="27" y={34 + i * 35} textAnchor="end">{Math.round(top * (4 - i) / 4)}</text></g>)}<polygon points={`42,170 ${line('arrivals')} ${x(s.history.length - 1)},170`} fill="url(#flow-fill)"/><polyline points={line('arrivals')} fill="none" stroke="#148b78" strokeWidth="2.5" strokeLinejoin="round"/><polyline points={line('discharges')} fill="none" stroke="#7895c8" strokeWidth="2.5" strokeDasharray="6 4" strokeLinejoin="round"/>{s.history.filter((_, i) => i === 0 || i === s.history.length - 1 || (s.history.length > 6 && i % 4 === 0)).map(p => <text key={p.minute} x={x(s.history.indexOf(p))} y="199" textAnchor="middle">{clock(p.minute)}</text>)}{s.history.length === 1 && <text x="318" y="100" textAnchor="middle" className="chart-empty">Run the simulation to see patient flow</text>}</svg></div>
}
export default App
