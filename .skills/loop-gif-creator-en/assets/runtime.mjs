// GIF89a encoder, global 3-3-2 palette. Bounded dictionary resets keep 9-bit codes.
export function validate(p){
 if(!p||!Number.isInteger(p.width)||!Number.isInteger(p.height)||p.width<16||p.height<16||p.width>512||p.height>512)throw Error('dimensions must be 16..512');
 if(!Number.isInteger(p.fps)||p.fps<5||p.fps>30||!Number.isInteger(p.frames)||p.frames<2||p.frames>120)throw Error('fps 5..30; frames 2..120');
 if(p.width*p.height*p.frames>6000000)throw Error('pixel budget exceeded');return p;
}
export function rgbaToIndexed(rgba,w,h){if(rgba.length!==w*h*4)throw Error('invalid RGBA length');const out=new Uint8Array(w*h);for(let i=0;i<out.length;i++){const a=rgba[i*4+3]/255;const rgb=[0,1,2].map(k=>Math.round(rgba[i*4+k]*a+255*(1-a)));out[i]=(rgb[0]>>5)<<5|(rgb[1]>>5)<<2|rgb[2]>>6;}return out;}
export function encode(frames,p){validate(p);if(frames.length!==p.frames||frames.some(f=>!(f instanceof Uint8Array)||f.length!==p.width*p.height))throw Error('indexed frame count/length mismatch');
 const out=[],byte=(...v)=>{for(const b of v)out.push(b);},u16=n=>byte(n&255,(n>>8)&255),str=s=>byte(...Array.from(s,c=>c.charCodeAt(0)));
 str('GIF89a');u16(p.width);u16(p.height);byte(0xf7,0,0);
 for(let i=0;i<256;i++)byte(Math.round(((i>>5)&7)*255/7),Math.round(((i>>2)&7)*255/7),Math.round((i&3)*255/3));
 byte(0x21,0xff,11);str('NETSCAPE2.0');byte(3,1,0,0,0);
 for(const frame of frames){byte(0x21,0xf9,4,4);u16(Math.max(1,Math.round(100/p.fps)));byte(0,0,0x2c);u16(0);u16(0);u16(p.width);u16(p.height);byte(0,8);
  const packed=[];let bits=0,n=0;const code=c=>{bits|=c<<n;n+=9;while(n>=8){packed.push(bits&255);bits>>>=8;n-=8;}};
  for(let i=0;i<frame.length;i++){if(i%120===0)code(256);code(frame[i]);}code(257);if(n)packed.push(bits&255);
  for(let i=0;i<packed.length;i+=255){const chunk=packed.slice(i,i+255);byte(chunk.length,...chunk);}byte(0);
 }byte(0x3b);return Uint8Array.from(out);
}
export function demoFrames(p){validate(p);return Array.from({length:p.frames},(_,i)=>{const a=new Uint8Array(p.width*p.height),phase=2*Math.PI*i/p.frames,cx=p.width/2,cy=p.height*0.5-Math.cos(phase)*p.height*0.15,r=p.width*(0.21+0.015*Math.sin(phase));
 for(let y=0;y<p.height;y++)for(let x=0;x<p.width;x++){let color=9;const dx=x-cx,dy=y-cy;if(dx*dx+dy*dy<(r+2)**2)color=0;if(dx*dx+dy*dy<r*r)color=252;if((dx+r*0.40)**2+(dy+r*0.55)**2<r*r*0.018)color=255;if(((dx+r*0.3)**2+(dy+r*0.15)**2<r*r*0.014)||((dx-r*0.3)**2+(dy+r*0.15)**2<r*r*0.014))color=0;if(Math.abs(Math.hypot(dx,dy-r*0.03)-r*0.40)<r*0.055&&dy>r*0.08)color=0;a[y*p.width+x]=color;}return a;});}
