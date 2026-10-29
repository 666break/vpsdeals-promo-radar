#!/usr/bin/env node
// audit.mjs — post-publish self-audit for a serverbudget.com article.
// Usage: node scripts/audit.mjs live-site/<page>.html [--expect-kw "vps price"]
import fs from 'node:fs';

const file = process.argv[2];
if (!file) { console.error('usage: node scripts/audit.mjs <file.html>'); process.exit(2); }
const html = fs.readFileSync(file, 'utf8');
let fail = 0;
const ok = (c, msg) => { console.log((c ? '  PASS  ' : '  FAIL  ') + msg); if (!c) fail++; };

// ---- title / description ----
const title = (html.match(/<title>([\s\S]*?)<\/title>/i) || [, ''])[1].trim();
const desc = (html.match(/<meta\s+name="description"\s+content="([\s\S]*?)"/i) || [, ''])[1].trim();
console.log('\n[meta]');
console.log('  title  (' + title.length + '): ' + title);
console.log('  desc   (' + desc.length + '): ' + desc);
ok(title.length > 0 && title.length <= 60, 'title <= 60 chars');
ok(desc.length > 0 && desc.length <= 160, 'description <= 160 chars');

// ---- canonical / og ----
const canon = (html.match(/<link rel="canonical" href="([^"]+)"/i) || [, ''])[1];
ok(!!canon, 'canonical present: ' + canon);

// ---- headings ----
const h1s = [...html.matchAll(/<h1[^>]*>([\s\S]*?)<\/h1>/gi)].map(m => m[1].replace(/<[^>]+>/g, '').trim());
const h2s = [...html.matchAll(/<h2[^>]*>([\s\S]*?)<\/h2>/gi)].map(m => m[1].replace(/<[^>]+>/g, '').trim());
const h3s = [...html.matchAll(/<h3[^>]*>([\s\S]*?)<\/h3>/gi)].map(m => m[1].replace(/<[^>]+>/g, '').trim());
console.log('\n[headings]');
console.log('  H1 x' + h1s.length + ' | H2 x' + h2s.length + ' | H3 x' + h3s.length);
ok(h1s.length === 1, 'exactly one H1');
ok(h2s.length >= 4, 'at least four H2 sections');
ok(h1s.length === 1 && h1s[0] === title, 'H1 matches title');

// ---- JSON-LD ----
console.log('\n[json-ld]');
const blocks = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/gi)].map(m => m[1]);
let types = [];
for (const [i, b] of blocks.entries()) {
  try { const j = JSON.parse(b); types.push(j['@type']); ok(true, 'block ' + (i + 1) + ' parses as JSON (' + j['@type'] + ')'); }
  catch (e) { ok(false, 'block ' + (i + 1) + ' invalid JSON: ' + e.message); }
}
for (const t of ['Article', 'BreadcrumbList', 'FAQPage']) ok(types.includes(t), 'has ' + t);

// FAQ answers must appear in the visible body (verbatim, whitespace-normalised)
const decode = (s) => s
  .replace(/&ldquo;|&rdquo;|&quot;/g, '"').replace(/&lsquo;|&rsquo;|&#39;/g, "'")
  .replace(/&mdash;/g, '-').replace(/&ndash;/g, '-').replace(/&middot;/g, '.')
  .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&nbsp;/g, ' ').replace(/&euro;/g, 'EUR').replace(/&pound;/g, 'GBP')
  .replace(/&divide;/g, '/').replace(/&times;/g, 'x').replace(/&minus;/g, '-')
  .replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d))
  .replace(/\s+/g, ' ');

const bodyText = decode(html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ')
  .replace(/<[^>]+>/g, ' '));
const faq = blocks.map(b => { try { return JSON.parse(b); } catch { return null; } }).find(j => j && j['@type'] === 'FAQPage');
if (faq) {
  let bad = 0;
  for (const q of faq.mainEntity) {
    const ans = decode(q.acceptedAnswer.text);
    const probe = ans.slice(0, 70).trim();
    if (!bodyText.includes(probe)) { bad++; console.log('  MISS  FAQ answer not found verbatim in body: ' + q.name); }
  }
  ok(bad === 0, 'FAQ answers appear in visible body (' + (faq.mainEntity.length - bad) + '/' + faq.mainEntity.length + ')');
}

// ---- tag balance ----
console.log('\n[structure]');
const voids = new Set(['meta', 'link', 'br', 'hr', 'img', 'input', 'source', 'path', 'rect', 'line', 'circle', 'polygon', 'text', 'use', 'stop', 'area', 'col', 'embed', 'param', 'track', 'wbr']);
const stack = [];
let unbalanced = null;
for (const m of html.matchAll(/<\/?([a-zA-Z][a-zA-Z0-9-]*)\b[^>]*?(\/?)>/g)) {
  const tag = m[1].toLowerCase();
  if (tag === '!doctype' || voids.has(tag) || m[2] === '/') continue;
  if (m[0].startsWith('</')) { const top = stack.pop(); if (top !== tag) { unbalanced = 'expected </' + top + '> got </' + tag + '>'; break; } }
  else stack.push(tag);
}
ok(unbalanced === null && stack.length === 0, 'tags balanced' + (unbalanced ? ' (' + unbalanced + ')' : ''));

// ---- language hygiene ----
console.log('\n[hygiene]');
const cjk = (html.match(/[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]/g) || []);
ok(cjk.length === 0, 'zero CJK characters (found ' + cjk.length + ')');
const videoWords = ['youtube', 'youtu.be', 'subscribe', 'watch the video', 'channel', 'podcast episode', 'video walkthrough'];
const hitV = videoWords.filter(w => new RegExp(w, 'i').test(bodyText));
ok(hitV.length === 0, 'no video/channel traces' + (hitV.length ? ' (' + hitV.join(', ') + ')' : ''));

// ---- body length ----
const words = bodyText.trim().split(/\s+/).filter(Boolean).length;
console.log('  body words: ' + words);
ok(words >= 900, 'body >= 900 words');

// ---- internal links ----
const links = [...html.matchAll(/href="(\/[^"#?]*)"/g)].map(m => m[1]);
const uniq = [...new Set(links)].filter(l => l !== '/');
console.log('  internal links: ' + uniq.join(' '));
ok(uniq.length >= 3, 'at least three internal links');

// ---- optional keyword presence ----
const kwIdx = process.argv.indexOf('--expect-kw');
if (kwIdx > -1) {
  const kw = process.argv[kwIdx + 1];
  ok(new RegExp(kw, 'i').test(title + ' ' + desc + ' ' + h1s.join(' ')), 'keyword "' + kw + '" appears in title/desc/h1');
}

console.log('\n' + (fail === 0 ? 'RESULT: ALL PASS' : 'RESULT: ' + fail + ' FAILURE(S)'));
process.exit(fail === 0 ? 0 : 1);
