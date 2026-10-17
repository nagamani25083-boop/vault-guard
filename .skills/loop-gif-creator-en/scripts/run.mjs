import fs from 'node:fs/promises';
const [input,out]=process.argv.slice(2);
if(!input||!out){console.error('Usage: node scripts/run.mjs input.json output-file');process.exit(2);}
try{const p=JSON.parse(await fs.readFile(input,'utf8'));const m=await import('../assets/runtime.mjs');let data;
if(m.render){const r=m.render(p);data=m.wav(r.samples,r.rate);}
else if(m.tsv)data=m.tsv(p);
else if(m.stl)data=out.endsWith('.scad')?m.scad(p):m.stl(p);
else data=m.encode(m.demoFrames(p),p);
await fs.writeFile(out,data,{flag:'wx'});console.log(JSON.stringify({output:out,bytes:(await fs.stat(out)).size}));
}catch(e){console.error(e.message);process.exit(1);}
