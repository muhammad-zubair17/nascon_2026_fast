import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getTopics, onboard, setUid, todayEdition } from '../api'

const ICONS = {
  AI: '🤖', Technology: '💻', World: '🌍', Pakistan: '🇵🇰', Business: '💼',
  Science: '🔬', Health: '🩺', Sports: '🏏', Entertainment: '🎬', Politics: '🏛️',
}
const IDEAS = ['machine learning', 'space', 'cricket', 'startups', 'climate',
  'cybersecurity', 'football', 'movies']

export default function Onboarding() {
  const nav = useNavigate()
  const [step, setStep] = useState(0)
  const [topics, setTopics] = useState([])
  const [name, setName] = useState('')
  const [picked, setPicked] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    getTopics().then(setTopics).catch(() => setErr('Cannot reach the server. Is the backend running?'))
  }, [])

  const toggle = (t) => setPicked((p) => (p.includes(t) ? p.filter((x) => x !== t) : [...p, t]))
  const addIdea = (i) => setText((t) => (t.toLowerCase().includes(i) ? t : (t ? t + ', ' : '') + i))

  async function finish() {
    setBusy(true)
    setErr('')
    try {
      const u = await onboard({ name: name.trim(), topics: picked, free_text: text })
      setUid(u.user_id)
      await todayEdition(u.user_id) // print the first edition now
      nav('/')
    } catch (e) {
      setErr('Something went wrong. Please try again.')
      setBusy(false)
    }
  }

  if (busy) {
    return (
      <div className="center">
        <h1 className="logo">The Daily You</h1>
        <p className="note">Setting the type for your first edition…</p>
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="onb">
      <h1 className="logo">The Daily You</h1>
      <p className="tagline">One paper. Made for you. Every morning.</p>
      <div className="dots">
        {[0, 1, 2].map((i) => <span key={i} className={i <= step ? 'on' : ''} />)}
      </div>

      {step === 0 && (
        <div className="card">
          <h2>First, what should we call you?</h2>
          <input autoFocus value={name} placeholder="Your name"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && name.trim() && setStep(1)} />
          <button className="btn" disabled={!name.trim()} onClick={() => setStep(1)}>Continue</button>
        </div>
      )}

      {step === 1 && (
        <div className="card">
          <h2>What do you want to read about, {name}?</h2>
          <p className="hint">Pick as many as you like.</p>
          <div className="chips">
            {topics.map((t) => (
              <button key={t} className={'chip' + (picked.includes(t) ? ' on' : '')} onClick={() => toggle(t)}>
                {ICONS[t] || '📰'} {t}
              </button>
            ))}
          </div>
          <div className="row">
            <button className="link" onClick={() => setStep(0)}>Back</button>
            <button className="btn" disabled={!picked.length} onClick={() => setStep(2)}>Continue</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <h2>Anything specific you're into?</h2>
          <p className="hint">This is how your paper gets sharp. Optional, but worth it.</p>
          <textarea rows={3} value={text} placeholder="e.g. machine learning, space, cricket…"
            onChange={(e) => setText(e.target.value)} />
          <div className="chips small">
            {IDEAS.map((i) => <button key={i} className="chip" onClick={() => addIdea(i)}>+ {i}</button>)}
          </div>
          {err && <p className="err">{err}</p>}
          <div className="row">
            <button className="link" onClick={() => setStep(1)}>Back</button>
            <button className="btn" onClick={finish}>Print my first edition</button>
          </div>
        </div>
      )}
      {step < 2 && err && <p className="err">{err}</p>}
    </div>
  )
}