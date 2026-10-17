/* eslint-disable @typescript-eslint/no-explicit-any -- validates untrusted JSON before it has a schema */
import { readFile, writeFile, stat } from 'node:fs/promises';
import { resolve, relative, join, isAbsolute } from 'node:path';
import { createHash } from 'node:crypto';

const digest = (text: string) => createHash('sha256').update(text).digest('hex');
const deterministicClasses = new Set(['ARCHITECTURE', 'DRAWIO', 'TIKZ', 'HTML', 'MERMAID']);
const completeTemplates = new Set(['template.sem_violin_pearson', 'template.shap_dependence', 'template.shap_contribution']);
function validSourceReference(value: unknown, renderer: string): boolean {
  if (typeof value !== 'string') return false;
  const normalized = value.replace(/^recipe:/, '');
  if (normalized.startsWith('template.')) return renderer === 'DATA' && completeTemplates.has(normalized);
  if (value.startsWith('asset:')) return renderer === 'ARCHITECTURE' && /^asset:VA-\d{3}$/.test(value);
  return /^(basic|advanced|empirical|competition|academic)\s*#\s*\d+$|^recipe:[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$|^custom$/.test(value);
}
function local(cwd: string, path: string) {
  const result = resolve(cwd, path), rel = relative(cwd, result);
  if (!rel || rel.startsWith('..') || isAbsolute(rel)) throw new Error('Plan sources must stay within the task workspace');
  return result;
}
export function figurePlanErrors(plan: any, minimum = 8): string[] {
  const errors: string[] = [], figures = Array.isArray(plan?.figures) ? plan.figures : [];
  const data = figures.filter((f: any) => f.class === 'DATA');
  if (data.length < Math.max(8, minimum)) errors.push(`DATA requires at least ${Math.max(8, minimum)} distinct figures (PDF/PNG and panels do not count separately)`);
  const ids = new Set();
  for (const f of figures) {
    if (!/^(fig_|tikz_|TABLE_)[a-z0-9_]+$/.test(f.id ?? '') || ids.has(f.id)) errors.push(`Invalid or duplicate figure id: ${f.id}`);
    if (f.class === 'TIKZ' && !String(f.id).startsWith('tikz_')) errors.push(`${f.id}: TikZ basename must start with tikz_`);
    if (f.class !== 'TIKZ' && String(f.id).startsWith('tikz_')) errors.push(`${f.id}: non-TikZ basename must start with fig_ or TABLE_`);
    ids.add(f.id);
    for (const k of ['chartType', 'reason', 'message', 'section', 'question', 'layout']) if (typeof f[k] !== 'string' || !f[k].trim()) errors.push(`${f.id}: missing ${k}`);
    if (!['DATA','TABLE','ARCHITECTURE','DRAWIO','TIKZ','ILLUSTRATION','HTML','MERMAID'].includes(f.class)) errors.push(`${f.id}: unsupported renderer class`);
    if (!validSourceReference(f.recipe, f.class)) errors.push(`${f.id}: recipe must identify a registered complete template, recipe:<id>, category #N, an ARCHITECTURE asset:VA-NNN, or custom`);
    if (!Array.isArray(f.sources) || !f.sources.length) errors.push(`${f.id}: sources required`);
    const extensions: Record<string, string[]> = { DATA:['pdf','png','svg'], TABLE:['tex','md','csv','html'], ARCHITECTURE:['pptx','svg','pdf','png'], DRAWIO:['drawio','pdf','png','svg'], TIKZ:['tex','pdf','png','svg'], ILLUSTRATION:['png','jpg','webp'], HTML:['html','pdf','png'], MERMAID:['mmd','pdf','svg','png'] };
    const supportedOutput = (p: unknown) => typeof p === 'string' && !p.split('/').includes('..') && (extensions[f.class] ?? []).some(ext =>
      p === `figures/${f.id}.${ext}` || (f.class === 'ARCHITECTURE' && p.startsWith(`figures/${f.id}/`) && p.endsWith(`.${ext}`)));
    if (!Array.isArray(f.outputs) || !f.outputs.some(supportedOutput)) errors.push(`${f.id}: outputs must include a supported artifact for its renderer`);
    if (!(f.finalWidthMm > 0)) errors.push(`${f.id}: finalWidthMm required`);
  }
  if (!figures.some((f: any) => deterministicClasses.has(f.class) && f.purpose === 'roadmap')) errors.push('Full plan requires one deterministic overall roadmap with purpose=roadmap in the selected format');
  if (!Array.isArray(plan?.questions) || !plan.questions.length) errors.push('questions classification required');
  for (const q of plan?.questions ?? []) {
    if (!q.id || !['reasoning','data','mixed'].includes(q.kind)) errors.push('Each question requires id and kind reasoning/data/mixed');
    if (!figures.some((f: any) => f.question === q.id)) errors.push(`${q.id}: no planned figure`);
    if (q.kind === 'reasoning' && !figures.some((f: any) => f.question === q.id && f.class === 'TIKZ' && f.purpose === 'derivation')) errors.push(`${q.id}: reasoning question requires true derivation construction`);
    if (q.spatial && !figures.some((f: any) => f.question === q.id && f.class === 'DATA' && f.spatial === true)) errors.push(`${q.id}: spatial evidence plot required`);
  }
  return errors;
}
export async function validateFigurePlan(cwd: string, planPath: string) {
  const policyPath = join(cwd, '.vivid/figure-plan-policy.json');
  const policy = JSON.parse(await readFile(policyPath, 'utf8').catch(() => '{"minimum":8}'));
  const text = await readFile(local(cwd, planPath), 'utf8'), plan = JSON.parse(text);
  const errors = figurePlanErrors(plan, policy.minimum ?? 8);
  for (const f of plan.figures ?? []) for (const source of f.sources ?? []) {
    try { if (!(await stat(local(cwd, source))).isFile()) throw new Error(); } catch { errors.push(`${f.id}: missing/nonlocal source ${source}`); }
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(policyPath, JSON.stringify({ ...policy, required: true, planPath, planHash: digest(text) }, null, 2));
  return { valid: true, figures: plan.figures.length, dataFigures: plan.figures.filter((f: any) => f.class === 'DATA').length, note: '18–30 DATA figures is a soft reference, not a quota. This validates the contract, not design quality.' };
}
export async function beginFigurePlan(cwd: string, minimum = 8) {
  if (!Number.isInteger(minimum) || minimum < 8) throw new Error('Minimum must be an integer >=8; raise only for an explicit user request');
  await writeFile(join(cwd, '.vivid/figure-plan-policy.json'), JSON.stringify({ required: true, minimum }, null, 2));
  return 'Read source material and bundled upstream-planning.md, then write FIGURE_PLAN.json. Run figure-plan-cli.mjs validate explicitly before rendering; shell and repair commands stay available.';
}
