import assert from 'node:assert/strict'
import test from 'node:test'
import { applyResponse, emptyDatabase, initializationRequest, isInitialization, readRequests, runRequests, send, sqlFor } from '../src/api.ts'
import type { Database, Payload, Request, Row } from '../src/api.ts'
import { baselineRefs, baselineProblems, finalStateMatches, fingerprint, populationPlan, testPlan } from '../src/demo.ts'

function server() {
  let data = emptyDatabase()
  let nextId = 40
  let initialized = false
  const sent: { path: string; method: string; body?: Payload }[] = []
  const fetcher = (async (url: string, options: RequestInit) => {
    const [, resource, rawId] = new URL(url, 'http://test').pathname.replace('/api', '').split('/')
    const key = resource as keyof Database
    const id = rawId ? Number(rawId) : undefined
    const method = options.method ?? 'GET'
    const body = options.body ? JSON.parse(String(options.body)) as Payload : undefined
    sent.push({ path: String(url), method, body })
    if (resource === 'initialization') {
      if (method === 'POST') initialized = true
      return Response.json({ was_initialized: initialized })
    }
    let result: Row | Row[] | null = null
    if (method === 'GET') result = id ? data[key].find(row => row.id === id) ?? null : data[key]
    else if (method === 'DELETE') {
      data[key] = data[key].filter(row => row.id !== id)
      return new Response(null, { status: 204 })
    } else {
      if (method === 'PATCH' && !data[key].some(row => row.id === id)) return Response.json({ detail: 'Not found' }, { status: 404 })
      result = { ...(id ? data[key].find(row => row.id === id) : {}), ...body, id: id ?? nextId++ } as Row
      if (key === 'patients') {
        const staff = data.staff.find(row => row.id === result?.staff_id)
        if (staff && staff.hospital_id !== result.hospital_id) return Response.json({ detail: 'Different hospital' }, { status: 400 })
      }
      data = applyResponse(data, { resource: key, method: method as Request['method'], id, body, title: '' }, result)
    }
    return Response.json(result, { status: method === 'POST' ? 201 : 200 })
  }) as typeof fetch
  return { fetcher, sent, data: () => data }
}
async function populate(mock: ReturnType<typeof server>) {
  await runRequests(populationPlan(mock.data()), {}, request => send(request, '/api', mock.fetcher))
  assert.ok(baselineRefs(mock.data()))
}
function logical(data: Database) {
  const hospital = (id: unknown) => data.hospitals.find(row => row.id === id)?.name
  const staff = (id: unknown) => data.staff.find(row => row.id === id)?.first_name ?? null
  return {
    hospitals: data.hospitals.map(row => [row.name, row.location, row.capacity]),
    roles: data.roles.map(row => [row.name, row.description, row.access_type]),
    staff: data.staff.map(row => [row.first_name, row.date_of_admission, row.last_check_in, row.salary, hospital(row.hospital_id), (row.role_ids as number[]).map(id => data.roles.find(role => role.id === id)?.name).sort()]),
    patients: data.patients.map(row => [row.first_name, row.last_name, row.date_of_birth, row.image_blob, hospital(row.hospital_id), staff(row.staff_id)]).sort(),
  }
}
test('population and test send JSON API requests and repeat the same logical final state', async () => {
  const mock = server()
  await populate(mock)
  const firstBaseline = logical(mock.data())
  const refs = baselineRefs(mock.data())!
  await runRequests(testPlan(), refs, request => send(request, '/api', mock.fetcher))
  assert.ok(finalStateMatches(mock.data(), refs))
  assert.equal(baselineRefs(mock.data()), null)
  const firstFinal = logical(mock.data())
  assert.equal(mock.data().patients.length, 5)
  assert.equal(mock.data().patients.filter(row => row.staff_id === null).length, 1)
  const transfer = mock.sent.find(request => request.method === 'PATCH' && request.body?.hospital_id)
  assert.ok(transfer?.body?.staff_id, 'Patient transfer sends hospital and staff together')
  await populate(mock)
  assert.deepEqual(logical(mock.data()), firstBaseline)
  const again = baselineRefs(mock.data())!
  assert.notEqual(again.olivia, refs.olivia, 'IDs come from the server, not hardcoded fixtures')
  await runRequests(testPlan(), again, request => send(request, '/api', mock.fetcher))
  assert.deepEqual(logical(mock.data()), firstFinal)
  assert.ok(finalStateMatches(mock.data(), again))
  assert.ok(mock.sent.every(request => !JSON.stringify(request.body ?? {}).includes('INSERT INTO')))
})
test('population preserves unrelated hospitals, roles, staff, and patients', async () => {
  const mock = server()
  const execute = (request: Request) => send(request, '/api', mock.fetcher)
  await runRequests([
    { resource: 'hospitals', method: 'POST', body: { name: 'Custom', location: 'Custom City', capacity: 5 }, bind: 'hospital', title: '' },
    { resource: 'roles', method: 'POST', body: { name: 'Custom role', access_type: 'C' }, bind: 'role', title: '' },
    { resource: 'staff', method: 'POST', body: { first_name: 'Pat', last_name: 'Custom', date_of_admission: '2024-01-15', last_check_in: null, salary: '1234.56', hospital_id: '$hospital', role_ids: ['$role'] }, bind: 'staff', title: '' },
    { resource: 'patients', method: 'POST', body: { first_name: 'Alex', last_name: 'Custom', date_of_birth: '1990-01-01', hospital_id: '$hospital', staff_id: '$staff' }, title: '' },
  ], {}, execute)
  const saved = structuredClone(mock.data())
  await populate(mock)
  await populate(mock)
  for (const key of Object.keys(saved) as (keyof Database)[]) {
    assert.deepEqual(mock.data()[key].filter(row => saved[key].some(record => record.id === row.id)), saved[key])
  }
})
test('baseline checks reject edited or extra demo records and final checks catch wrong assignments', async () => {
  assert.equal(baselineRefs(emptyDatabase()), null)
  const mock = server()
  await populate(mock)
  const extra = structuredClone(mock.data())
  extra.patients.push({ ...extra.patients[0], id: 999999 })
  assert.equal(baselineRefs(extra), null)
  const data = structuredClone(mock.data())
  const refs = baselineRefs(data)!
  data.patients[0].staff_id = null
  assert.equal(baselineRefs(data), null)
  await runRequests(testPlan(), refs, request => send(request, '/api', mock.fetcher))
  const final = structuredClone(mock.data())
  final.patients.find(row => row.first_name === 'Casey')!.staff_id = null
  assert.equal(finalStateMatches(final, refs), false)
})
test('failures stop the sequence, preserve committed operations, and never retry', async () => {
  const mock = server()
  let count = 0
  await assert.rejects(runRequests(populationPlan(mock.data()), {}, async request => {
    count += 1
    if (count === 2) throw new Error('Server unavailable')
    return send(request, '/api', mock.fetcher)
  }), /Server unavailable/)
  assert.equal(count, 2)
  assert.equal(mock.data().hospitals.length, 1)
  await populate(mock)
  assert.ok(baselineRefs(mock.data()))
})
test('reads, null PATCH, SQL previews, and server errors retain API semantics', async () => {
  const mock = server()
  await populate(mock)
  const refs = baselineRefs(mock.data())!
  const request: Request = { resource: 'patients', method: 'PATCH', id: refs.alex, body: { staff_id: null }, title: '' }
  assert.match(sqlFor(request), /staff_id = NULL/)
  await send(request, '/api/', mock.fetcher)
  assert.equal(mock.data().patients.find(row => row.id === refs.alex)!.staff_id, null)
  let loaded = emptyDatabase()
  for (const read of readRequests()) loaded = applyResponse(loaded, read, await send(read, '/api', mock.fetcher))
  assert.equal(fingerprint(loaded), fingerprint(mock.data()))
  await assert.rejects(send({ ...request, id: 999999 }, '/api', mock.fetcher), /404: Not found/)
  await assert.rejects(runRequests([{ ...request, id: '$missing' }], {}, async () => null), /Missing record reference/)
})

test('initialization is read from the backend and persists across client reloads without altering domain records', async () => {
  const mock = server()
  const initial = await send(initializationRequest(), '/api', mock.fetcher)
  assert.ok(isInitialization(initial))
  assert.equal(initial.was_initialized, false)
  await send(initializationRequest(true), '/api', mock.fetcher)
  const reloaded = await send(initializationRequest(), '/api', mock.fetcher)
  assert.ok(isInitialization(reloaded))
  assert.equal(reloaded.was_initialized, true)
  assert.deepEqual(mock.data(), emptyDatabase())
  await send(initializationRequest(true), '/api', mock.fetcher)
  assert.deepEqual(applyResponse(emptyDatabase(), initializationRequest(), reloaded), emptyDatabase())
  assert.throws(() => applyResponse(emptyDatabase(), initializationRequest(), []), /Invalid initialization/)
  assert.match(sqlFor(initializationRequest(true)), /ON DUPLICATE KEY UPDATE/)
})
test('population SQL foregrounds the concrete inserts and role links, without SELECTs', () => {
  const plan = populationPlan(emptyDatabase())
  const sql = plan.map(request => sqlFor(request, true)).join('\n')
  assert.ok(plan.every(request => request.method === 'POST'))
  assert.match(sql, /INSERT INTO hospital/)
  assert.match(sql, /Riverside Medical Center/)
  assert.match(sql, /INSERT INTO role/)
  assert.match(sql, /INSERT INTO staff/)
  assert.match(sql, /INSERT INTO staff_roles/)
  assert.match(sql, /INSERT INTO patient/)
  assert.match(sql, /1990-05-12/)
  assert.doesNotMatch(sql, /SELECT /)
})

test('baseline diagnostics identify the reported missing Olivia role assignment', async () => {
  const mock = server()
  await populate(mock)
  const broken = structuredClone(mock.data())
  broken.staff.find(row => row.first_name === 'Olivia')!.role_ids = []
  assert.equal(baselineRefs(broken), null)
  const problems = baselineProblems(broken)
  assert.equal(problems.length, 1)
  assert.match(problems[0], /staff Olivia Chen/)
  assert.match(problems[0], /role_ids/)
  assert.match(problems[0], /"role_ids":\[\]/)
})

test('new demo fields are fixed, images differ, and SQL previews decode BLOB values', async () => {
  const mock = server()
  await populate(mock)
  assert.deepEqual(mock.data().hospitals.map(row => row.capacity), [8, 4])
  assert.deepEqual(mock.data().roles.map(row => row.access_type), ['A', 'B', 'C'])
  assert.deepEqual(mock.data().staff.map(row => row.salary), ['7500.10', '4800.25', '8200.50'])
  for (const row of mock.data().staff) {
    assert.match(String(row.date_of_admission), /^\d{4}-\d{2}-\d{2}$/)
    assert.match(String(row.last_check_in), /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/)
  }
  const avatars = mock.data().patients.map(row => String(row.image_blob))
  assert.equal(new Set(avatars).size, 4)
  for (const image of avatars) assert.equal(Buffer.from(image, 'base64').subarray(0, 8).toString('hex'), '89504e470d0a1a0a')
  const refs = baselineRefs(mock.data())!
  await runRequests(testPlan(), refs, request => send(request, '/api', mock.fetcher))
  assert.equal(new Set(mock.data().patients.map(row => row.image_blob)).size, 5)
  const changed = structuredClone(mock.data())
  changed.staff[0].salary = '7500.11'
  assert.equal(finalStateMatches(changed, refs), false)
  assert.match(sqlFor({ resource: 'patients', method: 'PATCH', id: refs.alex, body: { image_blob: null }, title: 'Reset image' }), /image_blob = FROM_BASE64\('/)
  assert.match(sqlFor({ resource: 'patients', method: 'POST', body: { image_blob: avatars[0] }, title: 'Save image' }), /FROM_BASE64\('/)
})

test('dashboard GET requests bypass browser caches for reviews and persisted-state checks', async () => {
  const seen: RequestInit[] = []
  const fetcher = (async (_url: string, options: RequestInit) => {
    seen.push(options)
    return Response.json(options.method === 'GET' ? [] : { id: 1 })
  }) as typeof fetch
  for (const request of [...readRequests(), initializationRequest()]) await send(request, '/api', fetcher)
  assert.ok(seen.every(options => options.cache === 'no-store'))
  await send({ resource: 'roles', method: 'POST', body: { name: 'Example', access_type: 'A' }, title: '' }, '/api', fetcher)
  assert.equal(seen.at(-1)!.cache, undefined)
})
