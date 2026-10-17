const j = async (r) => {
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
const post = (url, body) =>
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  }).then(j)

export const getTopics = () => fetch('/api/topics').then(j)
export const onboard = (body) => post('/api/onboard', body)
export const todayEdition = (uid) => post(`/api/users/${uid}/edition`)
export const getEdition = (id) => fetch(`/api/editions/${id}`).then(j)
export const getArchive = (uid) => fetch(`/api/users/${uid}/editions`).then(j)
export const logEvent = (uid, article_id, type) =>
  fetch(`/api/users/${uid}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ article_id, type }),
    keepalive: true,
  }).catch(() => {})

export const getUid = () => localStorage.getItem('uid')
export const setUid = (id) => localStorage.setItem('uid', String(id))
export const clearUid = () => localStorage.removeItem('uid')