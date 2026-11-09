/* Course Markdown: lessons, explanations, with KaTeX formulas.
 *
 * The content is written in the repository and reviewed, but it still never
 * reaches the page as raw HTML: `html: false` escapes any tag, and
 * markdown-it refuses `javascript:` links. What comes out is markdown-it's own
 * HTML plus KaTeX's, both built from escaped text.
 *
 * Formulas: `$…$` inline, `$$…$$` on lines of their own for a display block.
 * A dollar sign inside code stays a dollar sign: code is parsed first.
 *
 * Interactive pieces: a fenced block ```simulator name``` becomes its own
 * block, so the page can mount a component there instead of HTML.
 */

import katex from 'katex'
import MarkdownIt from 'markdown-it'
import type { MarkdownIt as Markdown, StateBlock, StateInline } from 'markdown-it'

export type CourseBlock = { type: 'html'; html: string } | { type: 'simulator'; name: string }

function renderMath(source: string, displayMode: boolean): string {
  // `throwOnError: false`: a typo in a formula shows the formula in red,
  // it does not break the whole lesson
  return katex.renderToString(source, { displayMode, throwOnError: false, output: 'html' })
}

function mathInline(state: StateInline, silent: boolean): boolean {
  const start = state.pos
  if (state.src.charCodeAt(start) !== 0x24 /* $ */) return false
  // `$$` inline is not ours, and `$ ` after the opening reads as a price
  if (state.src.charCodeAt(start + 1) === 0x24) return false
  if (/\s/.test(state.src.charAt(start + 1))) return false

  // The closing `$`: the next one not escaped as `\$`, with no space before it
  let end = state.src.indexOf('$', start + 1)
  while (end !== -1 && state.src.charCodeAt(end - 1) === 0x5c /* \ */) {
    end = state.src.indexOf('$', end + 1)
  }
  if (end === -1 || end >= state.posMax) return false
  if (/\s/.test(state.src.charAt(end - 1))) return false

  if (!silent) {
    const token = state.push('math_inline', 'math', 0)
    token.content = state.src.slice(start + 1, end)
  }
  state.pos = end + 1
  return true
}

function mathBlock(
  state: StateBlock,
  startLine: number,
  endLine: number,
  silent: boolean,
): boolean {
  const first = state.src.slice(
    state.bMarks[startLine]! + state.tShift[startLine]!,
    state.eMarks[startLine],
  )
  if (!first.startsWith('$$')) return false
  if (silent) return true

  // `$$ x $$` on one line, or `$$` … `$$` around several
  const sameLine = first.length > 2 && first.trimEnd().endsWith('$$')
  let line = startLine
  let content: string
  if (sameLine) {
    content = first.trim().slice(2, -2)
  } else {
    const lines = [first.slice(2)]
    let closed = false
    while (++line < endLine) {
      const text = state.src.slice(state.bMarks[line]! + state.tShift[line]!, state.eMarks[line])
      if (text.trimEnd().endsWith('$$')) {
        lines.push(text.trimEnd().slice(0, -2))
        closed = true
        break
      }
      lines.push(text)
    }
    if (!closed) return false
    content = lines.join('\n')
  }

  const token = state.push('math_block', 'math', 0)
  token.block = true
  token.content = content.trim()
  token.map = [startLine, line + 1]
  state.line = line + 1
  return true
}

export function createCourseMarkdown(): Markdown {
  const md = new MarkdownIt({ html: false, linkify: true, typographer: false })
  md.inline.ruler.after('escape', 'math_inline', mathInline)
  md.block.ruler.after('blockquote', 'math_block', mathBlock, {
    alt: ['paragraph', 'reference', 'blockquote', 'list'],
  })
  md.renderer.rules.math_inline = (tokens, idx) => renderMath(tokens[idx]!.content, false)
  md.renderer.rules.math_block = (tokens, idx) =>
    `<div class="course-math">${renderMath(tokens[idx]!.content, true)}</div>\n`

  // Links out of the course open beside it, and leak nothing about the page
  const defaultLinkOpen =
    md.renderer.rules.link_open ??
    ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))
  md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
    const href = String(tokens[idx]!.attrGet('href') ?? '')
    if (/^https?:\/\//.test(href)) {
      tokens[idx]!.attrSet('target', '_blank')
      tokens[idx]!.attrSet('rel', 'noopener noreferrer')
    }
    return defaultLinkOpen(tokens, idx, options, env, self)
  }
  return md
}

let shared: Markdown | null = null

function courseMarkdown(): Markdown {
  shared ??= createCourseMarkdown()
  return shared
}

const SIMULATOR = /^simulator\s+([a-z][a-z0-9-]*)\s*$/

/* A lesson as a list of blocks: HTML, with a simulator wherever the text
 * places one */
export function renderCourse(source: string): CourseBlock[] {
  const md = courseMarkdown()
  const tokens = md.parse(source, {})
  const blocks: CourseBlock[] = []
  let pending: typeof tokens = []

  const flush = () => {
    if (pending.length) {
      blocks.push({ type: 'html', html: md.renderer.render(pending, md.options, {}) })
      pending = []
    }
  }
  for (const token of tokens) {
    const simulator = token.type === 'fence' ? SIMULATOR.exec(token.info.trim()) : null
    if (simulator) {
      flush()
      blocks.push({ type: 'simulator', name: simulator[1]! })
    } else {
      pending.push(token)
    }
  }
  flush()
  return blocks
}

/* A short text (an explanation, a question stem) rendered inline: formulas
 * and emphasis, no paragraph around it */
export function renderInline(source: string): string {
  return courseMarkdown().renderInline(source)
}
