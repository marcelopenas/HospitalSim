import type { Database, Payload, Refs, Request, Resource, Row } from './api.ts'

export const demoHospitals = [
  { key: 'riverside', name: '[Demo] Riverside Medical Center', location: '[Demo] Boston, Massachusetts' },
  { key: 'lakeside', name: '[Demo] Lakeside Clinic', location: '[Demo] Cambridge, Massachusetts' },
]
export const demoRoles = [
  { key: 'physician', name: '[Demo] Physician', description: 'Provides patient care' },
  { key: 'nurse', name: '[Demo] Nurse', description: 'Coordinates nursing care' },
  { key: 'coordinator', name: '[Demo] Shift coordinator', description: 'Coordinates the clinical shift' },
]
const baselineStaff = [
  { key: 'olivia', first_name: 'Olivia', last_name: 'Chen', hospital_id: '$riverside', role_ids: ['$physician'] },
  { key: 'noah', first_name: 'Noah', last_name: 'Patel', hospital_id: '$riverside', role_ids: ['$nurse'] },
  { key: 'mia', first_name: 'Mia', last_name: 'Brooks', hospital_id: '$lakeside', role_ids: ['$physician'] },
]
const baselinePatients = [
  { key: 'alex', first_name: 'Alex', last_name: 'Taylor', date_of_birth: '1990-05-12', hospital_id: '$riverside', staff_id: '$olivia' },
  { key: 'sam', first_name: 'Sam', last_name: 'Rivera', date_of_birth: '1985-03-21', hospital_id: '$riverside', staff_id: '$noah' },
  { key: 'jamie', first_name: 'Jamie', last_name: 'Morgan', date_of_birth: '2000-11-02', hospital_id: '$riverside', staff_id: null },
  { key: 'casey', first_name: 'Casey', last_name: 'Lee', date_of_birth: '1975-07-19', hospital_id: '$lakeside', staff_id: '$mia' },
]
export function populationPlan(data: Database): Request[] {
  const ids = new Set(data.hospitals.filter(row => demoHospitals.some(h => h.name === row.name)).map(row => row.id))
  const plan: Request[] = []
  // Only the two reserved demo hospitals are reset; unrelated hospitals remain intact.
  for (const resource of ['patients', 'staff'] as const) {
    for (const row of [...data[resource]].sort((a, b) => a.id - b.id)) {
      if (ids.has(Number(row.hospital_id))) plan.push({ resource, method: 'DELETE', id: row.id, title: `Reset demo ${resource} record #${row.id}: ${row.first_name} ${row.last_name}` })
    }
  }
  for (const [resource, fixtures] of [['hospitals', demoHospitals], ['roles', demoRoles]] as const) {
    for (const fixture of fixtures) {
      const { key, ...body } = fixture
      const current = data[resource].find(row => row.name === body.name)
      plan.push({ resource, method: current ? 'PATCH' : 'POST', id: current?.id, body, bind: key, title: `Restore ${body.name}` })
    }
  }
  for (const [resource, fixtures] of [['staff', baselineStaff], ['patients', baselinePatients]] as const) {
    for (const { key, ...body } of fixtures) plan.push({ resource, method: 'POST', body, bind: key, title: `Add ${body.first_name} ${body.last_name}` })
  }
  return plan
}
function matchingRow(resource: Resource, fixture: Payload, data: Database, refs: Refs): Row | undefined {
  return data[resource].find(row => Object.entries(fixture).every(([field, value]) => {
    const expected = typeof value === 'string' && value.startsWith('$') ? refs[value.slice(1)] : Array.isArray(value) ? value.map(v => typeof v === 'string' ? refs[v.slice(1)] : v).sort() : value
    return JSON.stringify(Array.isArray(row[field]) ? [...row[field]].sort() : row[field]) === JSON.stringify(expected)
  }))
}
function inspectBaseline(data: Database): { refs: Refs; problems: string[] } {
  const refs: Refs = {}
  const problems: string[] = []
  for (const [resource, fixtures] of [['hospitals', demoHospitals], ['roles', demoRoles], ['staff', baselineStaff], ['patients', baselinePatients]] as const) {
    for (const { key, ...fixture } of fixtures) {
      const exact = matchingRow(resource, fixture, data, refs)
      const fields: Payload = fixture
      const identity = (row: Row) => fields.name ? row.name === fields.name : row.first_name === fields.first_name && row.last_name === fields.last_name
      const named = data[resource].find(row => identity(row) && (!fields.hospital_id || row.hospital_id === refs[String(fields.hospital_id).slice(1)])) ?? data[resource].find(identity)
      const row = exact ?? named
      if (row) refs[key] = row.id
      if (!exact) {
        const resolve = (value: string | number | null) => typeof value === 'string' && value.startsWith('$') ? refs[value.slice(1)] ?? value : value
        const expected = Object.fromEntries(Object.entries(fields).map(([field, value]) => [field, Array.isArray(value) ? value.map(resolve) : resolve(value)]))
        problems.push(`${resource} ${fields.name ?? `${fields.first_name} ${fields.last_name}`}: expected ${JSON.stringify(expected)}; received ${row ? JSON.stringify(row) : 'no matching record'}`)
      }
    }
  }
  const ids = new Set([refs.riverside, refs.lakeside].filter(id => id !== undefined))
  for (const [resource, count] of [['staff', 3], ['patients', 4]] as const) {
    const actual = data[resource].filter(row => ids.has(Number(row.hospital_id))).length
    if (actual !== count) problems.push(`Demo ${resource}: expected ${count} records, received ${actual}`)
  }
  return { refs, problems }
}
export function baselineRefs(data: Database): Refs | null {
  const result = inspectBaseline(data)
  return result.problems.length ? null : result.refs
}
export function baselineProblems(data: Database): string[] { return inspectBaseline(data).problems }
export function testPlan(): Request[] {
  return [
    { hour: 8, resource: 'patients', method: 'POST', title: '08:00 · Admit Avery Stone at Riverside under Olivia Chen.', body: { first_name: 'Avery', last_name: 'Stone', date_of_birth: '1995-01-15', hospital_id: '$riverside', staff_id: '$olivia' } },
    { hour: 9, resource: 'patients', method: 'PATCH', id: '$jamie', title: '09:00 · Assign Jamie Morgan to Noah Patel.', body: { staff_id: '$noah' } },
    { hour: 10, resource: 'patients', method: 'PATCH', id: '$casey', title: '10:00 · Transfer Casey Lee to Riverside and Olivia Chen together.', body: { hospital_id: '$riverside', staff_id: '$olivia' } },
    { hour: 11, resource: 'patients', method: 'DELETE', id: '$sam', title: '11:00 · Discharge Sam Rivera by removing the current patient record.' },
    { hour: 12, resource: 'patients', method: 'POST', title: '12:00 · Admit Riley Quinn at Lakeside under Mia Brooks.', body: { first_name: 'Riley', last_name: 'Quinn', date_of_birth: '1988-09-23', hospital_id: '$lakeside', staff_id: '$mia' } },
    { hour: 13, resource: 'patients', method: 'PATCH', id: '$alex', title: '13:00 · Clear Alex Taylor’s clinician assignment.', body: { staff_id: null } },
    { hour: 14, resource: 'staff', method: 'PATCH', id: '$mia', title: '14:00 · Give Mia Brooks the additional shift coordinator role.', body: { role_ids: ['$physician', '$coordinator'] } },
    { hour: 15, resource: 'hospitals', method: 'PATCH', id: '$riverside', title: '15:00 · Update Riverside’s location to its North campus.', body: { location: '[Demo] Boston, North campus' } },
  ]
}
export function fingerprint(data: Database): string {
  return JSON.stringify(Object.fromEntries(Object.entries(data).map(([key, rows]) => [key, [...rows].sort((a, b) => a.id - b.id).map(row => Object.fromEntries(Object.entries(row).sort(([a], [b]) => a.localeCompare(b)).map(([k, v]) => [k, Array.isArray(v) ? [...v].sort((a, b) => a - b) : v])))])))
}
export function finalStateMatches(data: Database, refs: Refs): boolean {
  const ids = new Set([refs.riverside, refs.lakeside])
  const expectedPatients: Payload[] = baselinePatients.filter(p => p.key !== 'sam').map(({ key, ...patient }) => ({ ...patient, ...(key === 'jamie' ? { staff_id: '$noah' } : key === 'casey' ? { hospital_id: '$riverside', staff_id: '$olivia' } : key === 'alex' ? { staff_id: null } : {}) }))
  expectedPatients.push(
    { first_name: 'Avery', last_name: 'Stone', date_of_birth: '1995-01-15', hospital_id: '$riverside', staff_id: '$olivia' },
    { first_name: 'Riley', last_name: 'Quinn', date_of_birth: '1988-09-23', hospital_id: '$lakeside', staff_id: '$mia' },
  )
  return data.patients.filter(row => ids.has(Number(row.hospital_id))).length === 5
    && data.staff.filter(row => ids.has(Number(row.hospital_id))).length === 3
    && expectedPatients.every(patient => matchingRow('patients', patient, data, refs))
    && baselineStaff.every(({ key, ...person }) => matchingRow('staff', { ...person, ...(key === 'mia' ? { role_ids: ['$physician', '$coordinator'] } : {}) }, data, refs))
    && demoHospitals.every(({ key, ...h }) => matchingRow('hospitals', { ...h, ...(key === 'riverside' ? { location: '[Demo] Boston, North campus' } : {}) }, data, refs))
    && demoRoles.every(({ key: _key, ...role }) => matchingRow('roles', role, data, refs))
}
