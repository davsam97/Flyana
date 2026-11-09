/* The course's fixed parts: its one path and the icon of each module */

export const COURSE_PATH = 'aerospace-basics'

/* Spelled out here, not stored with the content: the icon bundle only ships
 * the `lucide:*` names it finds in the sources */
const MODULE_ICONS: Record<string, string> = {
  aerodynamics: 'lucide:wind',
  'flight-mechanics': 'lucide:plane',
  propulsion: 'lucide:flame',
  'orbital-mechanics': 'lucide:orbit',
  'space-systems': 'lucide:satellite',
  avionics: 'lucide:cpu',
  history: 'lucide:landmark',
}

export function moduleIcon(slug: string): string {
  return MODULE_ICONS[slug] ?? 'lucide:book-open'
}

/* A ratio from the API ("0.8", "1.000") as a whole percentage */
export function percent(ratio: string | number): number {
  return Math.round(Number(ratio) * 100)
}

/* A number typed by a student: French decimal comma, spaces between
 * thousands, `e` notation. Null when it is not a number */
export function parseNumber(input: string): string | null {
  const cleaned = input
    .trim()
    .replace(/[\s\u00a0\u202f]/g, '')
    .replace(',', '.')
  if (!/^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(cleaned)) return null
  return cleaned
}
