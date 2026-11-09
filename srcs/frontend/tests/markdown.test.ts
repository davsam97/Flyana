import { describe, expect, it } from 'vitest'

import { renderCourse, renderInline } from '../app/utils/markdown'

function html(source: string): string {
  return renderCourse(source)
    .map((block) => (block.type === 'html' ? block.html : `[${block.name}]`))
    .join('')
}

describe('course markdown', () => {
  it('renders an inline formula with KaTeX', () => {
    const out = html('La vitesse vaut $v = \\sqrt{\\mu / r}$ sur une orbite circulaire.')
    expect(out).toContain('class="katex"')
    expect(out).not.toContain('$v')
  })

  it('renders a display formula on its own lines', () => {
    const out = html(
      'Tsiolkovski :\n\n$$\n\\Delta v = I_{sp} g_0 \\ln \\frac{m_0}{m_f}\n$$\n\nFin.',
    )
    expect(out).toContain('class="course-math"')
    expect(out).toContain('katex-display')
    expect(out).toContain('<p>Fin.</p>')
  })

  it('renders a display formula written on one line', () => {
    expect(html('$$E = mc^2$$')).toContain('katex-display')
  })

  it('leaves dollars in code and prices alone', () => {
    const out = html('Le symbole `$x$` reste du code, et 5 $ reste un prix.')
    expect(out).toContain('<code>$x$</code>')
    expect(out).not.toContain('katex')
  })

  it('keeps an escaped dollar', () => {
    expect(html('Un \\$ seul')).not.toContain('katex')
  })

  it('escapes raw HTML instead of rendering it', () => {
    const out = html('<script>alert(1)</script> <img src=x onerror=alert(1)>')
    expect(out).not.toContain('<script>')
    expect(out).not.toContain('<img')
    expect(out).toContain('&lt;script&gt;')
  })

  it('refuses javascript links', () => {
    expect(html('[clic](javascript:alert(1))')).not.toContain('href="javascript:')
  })

  it('opens outside links in a new tab without opener', () => {
    const out = html('[NASA](https://www.nasa.gov)')
    expect(out).toContain('target="_blank"')
    expect(out).toContain('rel="noopener noreferrer"')
  })

  it('does not throw on a broken formula', () => {
    expect(() => html('$\\frac{1}{$')).not.toThrow()
  })

  it('cuts a lesson around its simulators', () => {
    const blocks = renderCourse('Avant.\n\n```simulator tsiolkovsky\n```\n\nAprès.')
    expect(blocks.map((block) => block.type)).toEqual(['html', 'simulator', 'html'])
    expect(blocks[1]).toEqual({ type: 'simulator', name: 'tsiolkovsky' })
  })

  it('keeps an ordinary code fence as code', () => {
    const blocks = renderCourse('```python\nprint(1)\n```')
    expect(blocks).toHaveLength(1)
    expect(blocks[0]!.type).toBe('html')
  })

  it('renders short texts inline, without a paragraph', () => {
    const out = renderInline('Avec *μ* = $3{,}986 \\times 10^{14}$')
    expect(out.startsWith('<p>')).toBe(false)
    expect(out).toContain('<em>μ</em>')
    expect(out).toContain('katex')
  })
})
