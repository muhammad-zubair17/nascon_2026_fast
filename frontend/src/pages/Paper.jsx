import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { clearUid, getEdition, getUid, logEvent, todayEdition } from '../api'

function Story({ s, uid, onSkip, showImage }) {
  const [imgOk, setImgOk] = useState(true)
  return (
    <article className="story">
      {showImage && s.image_url && imgOk && (
        <img src={s.image_url} alt="" onError={() => setImgOk(false)} />
      )}
      <div className="kicker">{s.topic}</div>
      <h3 className="headline">
        <a href={s.url} target="_blank" rel="noopener noreferrer"
          onClick={() => logEvent(uid, s.id, 'click')}>{s.headline}</a>
      </h3>
      <p className="blurb">{s.blurb}</p>
      <div className="meta">
        <span>{s.source}</span>
        <button className="skip" onClick={() => onSkip(s.id)}>Not for me</button>
      </div>
    </article>
  )
}

export default function Paper() {
  const { id } = useParams()
  const nav = useNavigate()
  const uid = getUid()
  const [ed, setEd] = useState(null)
  const [err, setErr] = useState('')
  const [hidden, setHidden] = useState(new Set())

  useEffect(() => {
    if (!uid) { nav('/welcome', { replace: true }); return }
    setEd(null); setErr('')
    const req = id ? getEdition(id) : todayEdition(uid)
    req.then(setEd).catch((e) => {
      if (e.status === 404 && !id) { clearUid(); nav('/welcome', { replace: true }) }
      else setErr('Could not load your paper. Is the backend running?')
    })
  }, [id])

  if (err) return <div className="center"><p className="err">{err}</p></div>
  if (!ed) {
    return (
      <div className="center">
        <h1 className="logo">The Daily You</h1>
        <p className="note">Setting the type…</p>
        <div className="spinner" />
      </div>
    )
  }

  const c = ed.content
  const skip = (sid) => {
    logEvent(uid, sid, 'skip')
    setHidden((h) => new Set(h).add(sid))
  }
    const refresh = () => {
    setEd(null)
    setHidden(new Set())
    todayEdition(uid, true).then(setEd).catch(() => setErr('Could not refresh.'))
  }
  const pick = (role) => c.stories.filter((s) => s.role === role && !hidden.has(s.id))
  const hero = pick('hero')[0]
  const date = new Date(c.date + 'T00:00:00').toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })

  return (
    <div className="page">
      <header className="masthead">
        <h1 className="logo">{c.paper_name}</h1>
      </header>
      <div className="dateline">
        <span>{date} · Prepared for {c.reader}</span>
        <nav>
          <Link to="/">Today</Link>
          <Link to="/archive">Archive</Link>
          {!id && (
            <a href="#" onClick={(e) => { e.preventDefault(); refresh() }}>Refresh paper</a>
          )}
          <a href={`/api/editions/${ed.id}/pdf`} target="_blank" rel="noopener noreferrer">
            Download PDF
          </a>
          <a href="#" onClick={(e) => { e.preventDefault(); clearUid(); nav('/welcome') }}>New reader</a>
        </nav>
      </div>

      {c.editor_note && <p className="note">{c.editor_note}</p>}

      <div className="front">
        <div className="main-col">
          {hero && <div className="hero"><Story s={hero} uid={uid} onSkip={skip} showImage /></div>}
          <div className="secondary">
            {pick('secondary').map((s) => <Story key={s.id} s={s} uid={uid} onSkip={skip} showImage />)}
          </div>
        </div>
        <aside>
          {c.three_things?.length > 0 && (
            <div className="box">
              <h3>3 things you learned today</h3>
              <ol>{c.three_things.map((t, i) => <li key={i}>{t}</li>)}</ol>
            </div>
          )}
          {pick('stretch').map((s) => (
            <div className="box stretch" key={s.id}>
              <h3>Outside your bubble</h3>
              <Story s={s} uid={uid} onSkip={skip} />
            </div>
          ))}
        </aside>
      </div>

      <section className="briefs">
        {pick('brief').map((s) => <Story key={s.id} s={s} uid={uid} onSkip={skip} />)}
      </section>
    </div>
  )
}