export async function api(path: string, options: RequestInit = {}) {
  const session = localStorage.getItem("session")

  const headers = {
    ...(options.headers || {}),
    Authorization: session ? `Bearer ${session}` : "",
    "Content-Type": "application/json",
  }

  const res = await fetch(path, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    localStorage.removeItem("session")
    window.location.reload()
  }

  return res.json()
}
