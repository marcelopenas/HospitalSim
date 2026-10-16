export type WardName = 'Emergency' | 'General medicine' | 'Intensive care' | 'Surgery'
export type Patient = { id: number; name: string; age: number; ward: WardName; status: 'In care' | 'Waiting' | 'Discharged'; admitted: number; duration: number; clinician: string }
export type Clinician = { name: string; role: string; ward: WardName }
export type Point = { minute: number; arrivals: number; discharges: number; occupied: number }
export type Event = { id: number; minute: number; text: string; type: 'arrival' | 'discharge' | 'system' }
export type Scenario = 'normal' | 'surge' | 'critical'
export type Simulation = { version: 1; hospital: number; minute: number; seed: number; nextId: number; patients: Patient[]; history: Point[]; events: Event[]; arrivals: number; discharges: number }
export const wards: WardName[] = ['Emergency', 'General medicine', 'Intensive care', 'Surgery']
export const hospitals = [
  { name: 'Riverside Medical Center', location: 'Boston, Massachusetts', capacities: [18, 32, 10, 20], staff: 24 },
  { name: 'Northview Community Hospital', location: 'Cambridge, Massachusetts', capacities: [12, 24, 6, 14], staff: 16 },
]
export const clinicians: Clinician[] = [
  { name: 'Dr. Olivia Chen', role: 'Physician', ward: 'Emergency' },
  { name: 'Dr. James Wilson', role: 'Physician', ward: 'General medicine' },
  { name: 'Dr. Amara Okafor', role: 'Intensivist', ward: 'Intensive care' },
  { name: 'Dr. Ethan Park', role: 'Surgeon', ward: 'Surgery' },
  { name: 'Sofia Martinez', role: 'Registered nurse', ward: 'Emergency' },
  { name: 'Noah Thompson', role: 'Registered nurse', ward: 'General medicine' },
  { name: 'Isabella Lee', role: 'Registered nurse', ward: 'Intensive care' },
  { name: 'Lucas Brown', role: 'Registered nurse', ward: 'Surgery' },
]
const firstNames = ['Emma', 'Liam', 'Charlotte', 'Oliver', 'Amelia', 'Henry', 'Mia', 'Theodore', 'Ava', 'Benjamin', 'Harper', 'Daniel', 'Evelyn', 'Samuel', 'Luna', 'Alexander']
const lastNames = ['Bennett', 'Reed', 'Morgan', 'Hayes', 'Brooks', 'Parker', 'Sullivan', 'Cooper', 'Rivera', 'Foster', 'Mitchell', 'Collins', 'Wright', 'Patel', 'Adams', 'Walker']
export function clock(minute: number) {
  return `${String(Math.floor(minute / 60) % 24).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`
}
export function day(minute: number) { return Math.floor(minute / 1440) + 1 }
export function capacity(hospital: number) { return hospitals[hospital].capacities.reduce((a, b) => a + b, 0) }
export function wardCount(s: Simulation, ward: WardName) { return s.patients.filter(p => p.ward === ward && p.status === 'In care').length }
export function occupied(s: Simulation) { return s.patients.filter(p => p.status === 'In care').length }
function random(s: Simulation) { s.seed = (s.seed * 1664525 + 1013904223) >>> 0; return s.seed / 4294967296 }
function log(s: Simulation, text: string, type: Event['type']) {
  s.events.unshift({ id: s.nextId++, minute: s.minute, text, type })
  s.events = s.events.slice(0, 40)
}
function createPatient(s: Simulation, name?: string, age?: number, ward?: WardName): Patient {
  const selectedWard = ward ?? wards[Math.floor(random(s) * wards.length)]
  return { id: s.nextId++, name: name ?? `${firstNames[Math.floor(random(s) * firstNames.length)]} ${lastNames[Math.floor(random(s) * lastNames.length)]}`, age: age ?? 18 + Math.floor(random(s) * 70), ward: selectedWard, status: wardCount(s, selectedWard) < hospitals[s.hospital].capacities[wards.indexOf(selectedWard)] ? 'In care' : 'Waiting', admitted: s.minute, duration: 60 + Math.floor(random(s) * 420), clinician: clinicians[wards.indexOf(selectedWard)].name }
}
export function initialSimulation(hospital = 0): Simulation {
  const s: Simulation = { version: 1, hospital, minute: 480, seed: 104729 + hospital, nextId: 1000, patients: [], history: [], events: [], arrivals: 0, discharges: 0 }
  const counts = hospital === 0 ? [12, 23, 7, 12] : [8, 17, 4, 9]
  wards.forEach((ward, i) => {
    for (let n = 0; n < counts[i]; n++) {
      const p = createPatient(s, undefined, undefined, ward)
      p.admitted = 240 + Math.floor(random(s) * 230)
      p.duration = s.minute - p.admitted + 30 + Math.floor(random(s) * 360)
      s.patients.push(p)
    }
  })
  s.history.push({ minute: s.minute, arrivals: 0, discharges: 0, occupied: occupied(s) })
  log(s, 'Day shift started. All departments are operational.', 'system')
  return s
}
function promoteWaiting(s: Simulation) {
  s.patients.forEach(p => {
    if (p.status === 'Waiting' && wardCount(s, p.ward) < hospitals[s.hospital].capacities[wards.indexOf(p.ward)]) {
      p.status = 'In care'; p.admitted = s.minute
      log(s, `${p.name} assigned a bed in ${p.ward.toLowerCase()}.`, 'system')
    }
  })
}
function recordPoint(s: Simulation) {
  const point = { minute: s.minute, arrivals: s.arrivals, discharges: s.discharges, occupied: occupied(s) }
  if (s.history.at(-1)?.minute === s.minute) s.history[s.history.length - 1] = point
  else s.history.push(point)
  s.history = s.history.slice(-25)
}
export function admit(s: Simulation, name: string, age: number, ward: WardName): Simulation {
  const next = structuredClone(s)
  const p = createPatient(next, name, age, ward)
  next.patients.push(p); next.arrivals++
  log(next, `${p.name} admitted to ${p.ward.toLowerCase()}${p.status === 'Waiting' ? ' queue' : ''}.`, 'arrival')
  recordPoint(next)
  return next
}
export function discharge(s: Simulation, id: number): Simulation {
  const next = structuredClone(s)
  const p = next.patients.find(p => p.id === id)
  if (!p || p.status !== 'In care') return s
  p.status = 'Discharged'; next.discharges++
  log(next, `${p.name} discharged from ${p.ward.toLowerCase()}.`, 'discharge')
  promoteWaiting(next)
  recordPoint(next)
  return next
}
export function step(s: Simulation, scenario: Scenario): Simulation {
  let next = structuredClone(s)
  next.minute += 15
  const dischargeIds = next.patients.filter(p => p.status === 'In care' && next.minute - p.admitted >= p.duration).map(p => p.id)
  dischargeIds.forEach(id => { next = discharge(next, id) })
  const count = (scenario === 'normal' ? 1 : scenario === 'surge' ? 4 : 7) + Math.floor(random(next) * 3)
  for (let i = 0; i < count; i++) {
    const p = createPatient(next)
    next.patients.push(p); next.arrivals++
    log(next, `${p.name} arrived at ${p.ward.toLowerCase()}${p.status === 'Waiting' ? ' (waiting for a bed)' : ''}.`, 'arrival')
  }
  recordPoint(next)
  // Preserve active patients and bound the completed-patient archive for long sessions.
  const active = next.patients.filter(p => p.status !== 'Discharged')
  const complete = next.patients.filter(p => p.status === 'Discharged').slice(-200)
  next.patients = [...complete, ...active]
  return next
}
export function advanceHour(s: Simulation, scenario: Scenario): Simulation {
  let next = s
  for (let i = 0; i < 4; i++) next = step(next, scenario)
  return next
}
