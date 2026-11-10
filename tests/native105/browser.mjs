// Preserve104 assertions and crash test, adapt UI fixture's now-required cartSave hook.
import fs from 'node:fs';
let src=fs.readFileSync('tests/native104/browser.mjs','utf8');
src=src.replaceAll('render(){},alert(){}','cartSave(){},render(){},alert(){}');
src=src.replace('await browser.close();',fs.readFileSync('tests/native105/browser-cases.mjs','utf8')+'\nawait browser.close();');
src=src.replaceAll('native104-browser.json','native105-browser.json');
const temp=new URL('./.browser-run.mjs',import.meta.url);fs.writeFileSync(temp,src);try{await import(temp.href)}finally{fs.unlinkSync(temp)}
