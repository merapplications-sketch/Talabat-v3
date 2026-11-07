import path from 'node:path';
import {verify} from './release-integrity.mjs';
import {checks} from './security-gate.mjs';
const root=path.resolve(import.meta.dirname,'..');
verify(root,[...checks.map(x=>x[0]),'headers','csp-report']);
console.log('PASS: exact source, tests, DB evidence and build bytes match the successful gate receipt');
