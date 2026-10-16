import test from 'node:test'
import assert from 'node:assert/strict'
import { admit, advanceHour, capacity, clock, day, discharge, hospitals, initialSimulation, occupied, step, wardCount, wards } from '../src/simulation.ts'
import type { Scenario } from '../src/simulation.ts'

test('initial state and seeded progression are reproducible and immutable', () => {
  const original = initialSimulation()
  const snapshot = structuredClone(original)
  assert.equal(occupied(original), 54)
  assert.equal(capacity(0), 80)
  assert.deepEqual(step(original, 'normal'), step(initialSimulation(), 'normal'))
  assert.deepEqual(original, snapshot)
  assert.equal(advanceHour(original, 'normal').minute, 540)
})
test('all scenarios preserve capacity and patient conservation across both hospitals', () => {
  for (const hospital of [0, 1]) {
    for (const scenario of ['normal', 'surge', 'critical'] as Scenario[]) {
      let s = initialSimulation(hospital)
      const baseline = occupied(s)
      for (let n = 0; n < 80; n++) {
        s = step(s, scenario)
        for (const [i, ward] of wards.entries()) assert.ok(wardCount(s, ward) <= hospitals[hospital].capacities[i])
        const active = s.patients.filter(p => p.status !== 'Discharged')
        assert.equal(active.length, baseline + s.arrivals - s.discharges)
        assert.equal(new Set(s.patients.map(p => p.id)).size, s.patients.length)
        assert.ok(s.history.length <= 25)
        assert.ok(s.events.length <= 40)
        assert.equal(s.history.at(-1)?.occupied, occupied(s))
      }
    }
  }
})
test('a full department queues arrivals and discharging promotes the oldest waiting patient', () => {
  let s = initialSimulation()
  const available = hospitals[0].capacities[0] - wardCount(s, 'Emergency')
  for (let n = 0; n <= available; n++) s = admit(s, `Test Patient ${n}`, 40, 'Emergency')
  const waiting = s.patients.find(p => p.status === 'Waiting')!
  assert.ok(waiting)
  const inCare = s.patients.find(p => p.status === 'In care' && p.ward === 'Emergency')!
  const before = structuredClone(s)
  const next = discharge(s, inCare.id)
  assert.deepEqual(s, before)
  assert.equal(next.patients.find(p => p.id === waiting.id)?.status, 'In care')
  assert.equal(wardCount(next, 'Emergency'), hospitals[0].capacities[0])
  assert.equal(next.discharges, 1)
  assert.equal(next.history.at(-1)?.discharges, 1)
  assert.deepEqual(discharge(next, inCare.id), next)
})
test('surge demand increases admissions; the clock crosses midnight correctly', () => {
  const normal = advanceHour(initialSimulation(), 'normal')
  const critical = advanceHour(initialSimulation(), 'critical')
  assert.ok(critical.arrivals > normal.arrivals)
  assert.equal(clock(1455), '00:15')
  assert.equal(day(1455), 2)
})
