import assert from 'node:assert/strict';import fs from 'node:fs/promises';import * as m from '../assets/runtime.mjs';
const p=JSON.parse(await fs.readFile(new URL('../assets/example.json',import.meta.url),'utf8'));
if(m.render){
 const r=m.render(p);assert.equal(r.samples.length,Math.ceil(p.bars*4*60/p.bpm*r.rate));assert(r.samples.some(x=>Math.abs(x)>0.01));assert(r.samples.every(x=>Number.isFinite(x)&&Math.abs(x)<1));assert.deepEqual(m.wav(r.samples,r.rate),m.wav(m.render(p).samples,r.rate));assert.throws(()=>m.render({...p,bpm:0}));assert.throws(()=>m.render({...p,bars:Infinity}));
 for(const style of ['ambient','lofi','dance'])assert(m.render({...p,style,bars:1}).samples.some(x=>x!==0));
 console.log('PASS music: duration, deterministic WAV, non-silent, headroom, 3 styles, invalid input');
}else if(m.tsv){
 m.validate(p);assert(m.tsv(p).includes(p.cards[0].front));assert.equal(m.select(p,{layer:'recall'}).length,1);assert.equal(m.select(p,{topic:'missing'}).length,0);assert.deepEqual(new Set(m.shuffle(p.cards)),new Set(p.cards));assert.throws(()=>m.validate({...p,cards:[p.cards[0],p.cards[0]]}));assert.throws(()=>m.validate({...p,cards:[{...p.cards[0],evidence:'invented'}]}));assert.throws(()=>m.validate({...p,cards:[]}));
 const storage={value:null,setItem(k,v){this.value=v;},getItem(){return this.value;}};m.saveState(storage,'deck',p,{favorites:[p.cards[0].id,'bad']});assert.deepEqual(m.loadState(storage,'deck').favorites,[p.cards[0].id]);storage.value='broken';assert.equal(m.loadState(storage,'deck').favorites.length,0);
 console.log('PASS flashcards: evidence, duplicates, layers, filter, shuffle, TSV, state restore, corrupt state');
}else if(m.stl){
 for(const width of [30,80,130]){const q={...p,width},a=m.inspect(m.mesh(q)),expected=q.width*q.depth*q.height-(q.width-2*q.wall)*(q.depth-2*q.wall)*(q.height-q.floor);assert(Math.abs(a.volumeMm3-expected)<1e-6);assert.equal(a.triangles,28);assert.deepEqual(a.bounds,[[0,0,0],[q.width,q.depth,q.height]]);}
 assert.throws(()=>m.mesh({...p,width:1}));assert.throws(()=>m.mesh({...p,wall:0.1}));assert.throws(()=>m.mesh({...p,buildVolume:[5,5,5]}));assert(m.scad(p).includes('difference()'));assert(m.stl(p).endsWith('endsolid tray\n'));
 console.log('PASS printing: 3 sizes, oriented watertight edges, analytic volume, bounds, nozzle, bed, STL/SCAD');
}else{
 const frames=m.demoFrames(p),b=m.encode(frames,p);assert.equal(new TextDecoder().decode(b.slice(0,6)),'GIF89a');assert.equal(b.at(-1),59);assert.notDeepEqual(frames[0],frames[Math.floor(p.frames/2)]);assert.deepEqual(b,m.encode(m.demoFrames(p),p));assert.throws(()=>m.encode([],p));assert.throws(()=>m.demoFrames({...p,width:99999}));assert.equal(m.rgbaToIndexed(new Uint8Array([0,0,0,0]),1,1)[0],255);
 console.log('PASS GIF: signature, trailer, varying frames, deterministic encoding, alpha flattening, input limits');
}
