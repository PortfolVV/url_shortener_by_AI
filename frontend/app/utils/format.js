const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

export function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return dateFormatter.format(date)
}

export function formatNumber(value) {
  return new Intl.NumberFormat('ru-RU').format(value ?? 0)
}

export function shortUrl(shortCode) {
  return `${window.location.origin}/l/${shortCode}`
}
