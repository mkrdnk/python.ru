// Compile the supplied design without changing its Figma-specific configuration.
import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {mkdtemp, readdir, readFile, writeFile, rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = path.join(root, 'redisign');
process.chdir(source);
const requireDesign = createRequire(path.join(source, 'package.json'));
const {build} = await import(pathToFileURL(requireDesign.resolve('vite')).href);
const {default: react} = await import(pathToFileURL(requireDesign.resolve('@vitejs/plugin-react')).href);
const {default: tailwind} = await import(pathToFileURL(requireDesign.resolve('@tailwindcss/vite')).href);
const output = await mkdtemp(path.join(os.tmpdir(), 'pythonru-design-'));
try {
  await build({root: source, configFile: false, plugins: [react(), tailwind()],
    build: {outDir: output, emptyOutDir: true}});
  const assets = path.join(output, 'assets');
  const files = (await readdir(assets)).filter(name => name.endsWith('.css')).sort();
  if (files.length !== 1) throw new Error('Expected one design stylesheet');
  const css = await readFile(path.join(assets, files[0]), 'utf8');
  await writeFile(path.join(root, 'assets/css/redisign.css'),
    '/* Generated from redisign/src/index.css; run node scripts/build-design.mjs. */\n' + css);
} finally {
  await rm(output, {recursive: true, force: true});
}
