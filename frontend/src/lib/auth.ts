type Tokens = { token: string; role: string }

const TOKEN_KEY = 'abs_token'
const ROLE_KEY = 'abs_role'

export function setTokens(token: string, role: string) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ROLE_KEY, role)
}

export function getTokens(): Tokens | null {
  const token = localStorage.getItem(TOKEN_KEY)
  const role = localStorage.getItem(ROLE_KEY)
  if (token && role) return { token, role }
  return null
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
}

