import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getArchive, getUid } from '../api'

export default function Archive() {
  const [items, setItems] = useState(null)
  useEffect(() => {
    getArchive(getUid()).then(setItems).catch(() => setItems([]))
  }, [])

  return (
    <div className="page">
      <header className="masthead"><h1 className="logo">The Daily You</h1></header>
      <div className="dateline"><span>Past editions</span><nav><Link to="/">Today</Link></nav></div>
      {!items && <p className="note">Loading…</p>}
      {items && !items.length && <p className="note">No editions yet.</p>}
      <ul className="archive">
        {items?.map((e) => (
          <li key={e.id}>
            <Link to={`/edition/${e.id}`}>
              <span className="kicker">
                {new Date(e.date + 'T00:00:00').toLocaleDateString('en-GB',
                  { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
              </span>
              <span className="headline">{e.headline}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}