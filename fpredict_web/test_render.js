import fs from 'fs';
import { transformSync } from 'esbuild';
const code = fs.readFileSync('src/routes/fixtures.tsx', 'utf-8');
const transformed = transformSync(code, { loader: 'tsx', jsx: 'automatic' }).code;
fs.writeFileSync('fixtures_transpiled.js', transformed);
