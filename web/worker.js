// Runs the Python randomizer (../momrando) in Pyodide, off the page's main thread.
// Messages in:  {type: 'run', bin: ArrayBuffer, name, opts, seed, ppf}
// Messages out: {type: 'status', text} | {type: 'ready', version} | {type: 'done', ...} | {type: 'error', text}
const PYODIDE = 'https://cdn.jsdelivr.net/npm/pyodide@0.29.5/';
importScripts(PYODIDE + 'pyodide.js');

let py = null;

async function init() {
  postMessage({type: 'status', text: 'Loading Python (about 10 MB, once)…'});
  py = await loadPyodide({indexURL: PYODIDE});
  postMessage({type: 'status', text: 'Loading the randomizer…'});
  const files = (await (await fetch('manifest.txt', {cache: 'no-cache'})).text()).split('\n').filter(Boolean);
  py.FS.mkdirTree('/home/pyodide/momrando/data');
  await Promise.all(files.map(async f => {
    const r = await fetch('../momrando/' + f, {cache: 'no-cache'});
    if (!r.ok) throw new Error('could not load momrando/' + f + ' (' + r.status + ')');
    py.FS.writeFile('/home/pyodide/momrando/' + f, new Uint8Array(await r.arrayBuffer()));
  }));
  const version = py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import momrando; momrando.__version__');
  postMessage({type: 'ready', version});
}

const RUN = `
import json, hashlib
from momrando.core import generate
from momrando.disc import make_ppf
opts = json.loads(OPTS)
src = open('/in.bin', 'rb').read()
out, d, spoiler = generate(src, opts, SEED)
open('/out.bin', 'wb').write(out)
if WANT_PPF:
    open('/out.ppf', 'wb').write(make_ppf(src, out, 'MoM DoG %s %s' % (d.version, SEED)))
del src
spoiler['options'] = opts
open('/spoiler.json', 'w').write(json.dumps(spoiler, indent=1, ensure_ascii=False))
json.dumps({'version': d.version, 'known': d.known_dump, 'md5_in': d.md5, 'md5_out': hashlib.md5(out).hexdigest()})
`;

async function run(m) {
  const FS = py.FS;
  for (const f of ['/in.bin', '/out.bin', '/out.ppf', '/spoiler.json']) { try { FS.unlink(f); } catch (e) {} }
  postMessage({type: 'status', text: 'Reading the disc image…'});
  FS.writeFile('/in.bin', new Uint8Array(m.bin));
  m.bin = null;
  postMessage({type: 'status', text: 'Patching… (this takes a little while)'});
  py.globals.set('OPTS', JSON.stringify(m.opts));
  py.globals.set('SEED', m.seed);
  py.globals.set('WANT_PPF', !!m.ppf);
  const info = JSON.parse(await py.runPythonAsync(RUN));
  FS.unlink('/in.bin');
  const take = f => { const a = FS.readFile(f); FS.unlink(f); return a; };
  const bin = take('/out.bin');
  const ppf = m.ppf ? take('/out.ppf') : null;
  const spoiler = new TextDecoder().decode(take('/spoiler.json'));
  const transfer = [bin.buffer]; if (ppf) transfer.push(ppf.buffer);
  postMessage({type: 'done', info, bin, ppf, spoiler}, transfer);
}

const ready = init().catch(e => postMessage({type: 'error', text: String(e && e.message || e)}));
onmessage = async ev => {
  await ready;
  try { await run(ev.data); }
  catch (e) {
    let t = String(e && e.message || e);
    const last = t.trim().split('\n').pop();          // Python traceback: show the last line first
    postMessage({type: 'error', text: last + (t.includes('\n') ? '\n\n' + t : '')});
  }
};
