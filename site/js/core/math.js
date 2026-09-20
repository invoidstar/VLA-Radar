/* VLA Radar local math renderer.
 * TeX delimiters are converted to native MathML; no CDN, eval, raw HTML or external font requests.
 */
'use strict';
(function(global){
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const greek={alpha:'α',beta:'β',gamma:'γ',delta:'δ',epsilon:'ϵ',varepsilon:'ε',zeta:'ζ',eta:'η',theta:'θ',vartheta:'ϑ',iota:'ι',kappa:'κ',lambda:'λ',mu:'μ',nu:'ν',xi:'ξ',pi:'π',varpi:'ϖ',rho:'ρ',varrho:'ϱ',sigma:'σ',varsigma:'ς',tau:'τ',upsilon:'υ',phi:'ϕ',varphi:'φ',chi:'χ',psi:'ψ',omega:'ω',Gamma:'Γ',Delta:'Δ',Theta:'Θ',Lambda:'Λ',Xi:'Ξ',Pi:'Π',Sigma:'Σ',Upsilon:'Υ',Phi:'Φ',Psi:'Ψ',Omega:'Ω'};
  const ops={
    cdot:'·',times:'×',div:'÷',pm:'±',mp:'∓',le:'≤',leq:'≤',ge:'≥',geq:'≥',neq:'≠',ne:'≠',approx:'≈',sim:'∼',simeq:'≃',
    equiv:'≡',propto:'∝',to:'→',rightarrow:'→',leftarrow:'←',leftrightarrow:'↔',Rightarrow:'⇒',Leftarrow:'⇐',Leftrightarrow:'⇔',
    in:'∈',notin:'∉',ni:'∋',subset:'⊂',subseteq:'⊆',supset:'⊃',supseteq:'⊇',cup:'∪',cap:'∩',setminus:'∖',
    land:'∧',lor:'∨',neg:'¬',forall:'∀',exists:'∃',partial:'∂',nabla:'∇',infty:'∞',ell:'ℓ',
    ldots:'…',cdots:'⋯',vdots:'⋮',ddots:'⋱',langle:'⟨',rangle:'⟩',vert:'|',Vert:'‖',mid:'∣'
  };
  const big={sum:'∑',prod:'∏',coprod:'∐',int:'∫',iint:'∬',iiint:'∭',oint:'∮',bigcup:'⋃',bigcap:'⋂'};
  const funcs=new Set(['sin','cos','tan','cot','sec','csc','arcsin','arccos','arctan','sinh','cosh','tanh','log','ln','exp','lim','min','max','argmin','argmax','det','dim','ker','Pr','softmax']);
  const variants={mathrm:'normal',mathbf:'bold',mathit:'italic',mathsf:'sans-serif',mathtt:'monospace',mathbb:'double-struck',mathcal:'script',boldsymbol:'bold-italic'};
  const accents={hat:'^',widehat:'^',bar:'¯',overline:'¯',vec:'→',tilde:'˜',widetilde:'˜',dot:'˙',ddot:'¨',underline:'_'};
  const delimiters={'{':'{','}':'}','[':'[',']':']','(':'(',')':')','|':'|','.':'','lbrace':'{','rbrace':'}','lbrack':'[','rbrack':']','langle':'⟨','rangle':'⟩','vert':'|','Vert':'‖','lvert':'|','rvert':'|','lVert':'‖','rVert':'‖'};

  function tag(name,body,attrs=''){return '<'+name+(attrs?' '+attrs:'')+'>'+body+'</'+name+'>';}
  function mo(v,attrs=''){return tag('mo',esc(v),attrs);}
  function mi(v,attrs=''){return tag('mi',esc(v),attrs);}
  function mn(v){return tag('mn',esc(v));}
  function mtext(v){return tag('mtext',esc(v));}

  class Parser{
    constructor(src){this.s=String(src||'');this.i=0;}
    peek(){return this.s[this.i]||'';}
    skip(){while(/\s/.test(this.peek()))this.i++;}
    command(){
      this.i++;
      if(this.peek()==='\\'){this.i++;return '\\';}
      const m=this.s.slice(this.i).match(/^[A-Za-z]+/);
      if(m){this.i+=m[0].length;return m[0];}
      return this.s[this.i++]||'';
    }
    rawGroup(open='{',close='}'){
      this.skip();if(this.peek()!==open)throw new Error('expected '+open);
      this.i++;let depth=1,start=this.i;
      while(this.i<this.s.length){
        const c=this.s[this.i++];
        if(c===open)depth++;
        else if(c===close&&--depth===0)return this.s.slice(start,this.i-1);
      }
      throw new Error('unclosed group');
    }
    group(){
      this.skip();
      if(this.peek()==='{'){const raw=this.rawGroup();return new Parser(raw).parse();}
      return this.atom(false);
    }
    delimiter(){
      this.skip();
      if(this.peek()==='\\'){const cmd=this.command();return delimiters[cmd]??ops[cmd]??cmd;}
      const c=this.peek();if(c)this.i++;return delimiters[c]??c;
    }
    matrix(env){
      const end='\\end{'+env+'}',at=this.s.indexOf(end,this.i);
      if(at<0)throw new Error('unclosed '+env);
      let raw=this.s.slice(this.i,at);this.i=at+end.length;
      if(env==='array'&&raw.trim().startsWith('{')){
        const p=new Parser(raw.trim()),spec=p.rawGroup();raw=p.s.slice(p.i);void spec;
      }
      const rows=raw.split(/\\\\/).map(r=>r.trim()).filter(Boolean);
      const table=tag('mtable',rows.map(row=>tag('mtr',row.split('&').map(cell=>tag('mtd',new Parser(cell.trim()).parse())).join(''))).join(''));
      const pair={pmatrix:['(',')'],bmatrix:['[',']'],Bmatrix:['{','}'],vmatrix:['|','|'],Vmatrix:['‖','‖'],cases:['{','']}[env];
      return pair?tag('mrow',mo(pair[0],'stretchy="true"')+table+(pair[1]?mo(pair[1],'stretchy="true"'):'')):table;
    }
    cmd(name){
      if(greek[name])return mi(greek[name]);
      if(Object.prototype.hasOwnProperty.call(delimiters,name))return mo(delimiters[name],'stretchy="true"');
      if(ops[name])return mo(ops[name]);
      if(big[name])return mo(big[name],'largeop="true" movablelimits="true"');
      if(funcs.has(name))return mi(name,'mathvariant="normal"');
      if(name==='frac'||name==='dfrac'||name==='tfrac')return tag('mfrac',tag('mrow',this.group())+tag('mrow',this.group()));
      if(name==='sqrt'){
        this.skip();
        if(this.peek()==='['){const idx=this.rawGroup('[',']');return tag('mroot',tag('mrow',this.group())+tag('mrow',new Parser(idx).parse()));}
        return tag('msqrt',tag('mrow',this.group()));
      }
      if(name==='text'||name==='textrm'||name==='textnormal')return mtext(this.rawGroup());
      if(name==='operatorname'){if(this.peek()==='*')this.i++;return mi(this.rawGroup(),'mathvariant="normal"');}
      if(name==='mathop')return tag('mrow',this.group());
      if(['displaystyle','textstyle','scriptstyle','scriptscriptstyle','limits','nolimits'].includes(name))return '';
      if(variants[name])return tag('mstyle',tag('mrow',this.group()),'mathvariant="'+variants[name]+'"');
      if(accents[name]){
        const base=tag('mrow',this.group()),mark=mo(accents[name],name==='vec'?'stretchy="true"':'');
        return name==='underline'?tag('munder',base+mark,'accentunder="true"'):tag('mover',base+mark,'accent="true"');
      }
      if(name==='left'||name==='right')return mo(this.delimiter(),'stretchy="true"');
      if(name==='begin'){const env=this.rawGroup();if(['matrix','pmatrix','bmatrix','Bmatrix','vmatrix','Vmatrix','cases','aligned','array'].includes(env))return this.matrix(env);return mtext('\\begin{'+env+'}');}
      if(['quad','qquad','enspace',';',' ',',','!'].includes(name))return '<mspace width="'+(name==='qquad'?'2em':name==='quad'?'1em':'.35em')+'"/>';
      if(name==='overbrace'||name==='underbrace'){const base=tag('mrow',this.group()),brace=mo(name==='overbrace'?'⏞':'⏟','stretchy="true"');return tag(name==='overbrace'?'mover':'munder',base+brace);}
      return mtext('\\'+name);
    }
    scriptArg(){
      this.skip();
      if(this.peek()==='{')return tag('mrow',new Parser(this.rawGroup()).parse());
      return this.atom(false)||mtext('');
    }
    scripts(base){
      let sub=null,sup=null;
      while(true){
        this.skip();const c=this.peek();
        if(c!=='_'&&c!=='^')break;
        this.i++;const arg=this.scriptArg();
        if(c==='_')sub=arg;else sup=arg;
      }
      if(sub&&sup)return tag('msubsup',base+sub+sup);
      if(sub)return tag('msub',base+sub);
      if(sup)return tag('msup',base+sup);
      return base;
    }
    atom(withScripts=true){
      this.skip();if(this.i>=this.s.length)return '';
      let base='',c=this.peek();
      if(c==='{'){base=tag('mrow',new Parser(this.rawGroup()).parse());}
      else if(c==='\\'){base=this.cmd(this.command());}
      else if(/[0-9]/.test(c)){
        const m=this.s.slice(this.i).match(/^\d+(?:\.\d+)?/)[0];this.i+=m.length;base=mn(m);
      }else if(/[A-Za-z]/.test(c)){
        const m=this.s.slice(this.i).match(/^[A-Za-z]+/)[0];this.i+=m.length;base=mi(m);
      }else{
        this.i++;
        if(/[+\-=<>*/,:;|()[\]]/.test(c))base=mo(c,'()[]|'.includes(c)?'stretchy="true"':'');
        else if(/[_^]/.test(c))base=mtext(c);
        else base=mi(c);
      }
      return withScripts?this.scripts(base):base;
    }
    parse(stop=''){
      let out='';
      while(this.i<this.s.length){
        if(stop&&this.peek()===stop)break;
        out+=this.atom(true);
      }
      return out||'<mrow></mrow>';
    }
  }

  function renderTex(tex,display=false){
    const raw=String(tex||'').trim();
    if(!raw)return '';
    try{
      const body=new Parser(raw).parse();
      const math='<math xmlns="http://www.w3.org/1998/Math/MathML" display="'+(display?'block':'inline')+'" aria-label="'+esc(raw)+'"><semantics><mrow>'+body+'</mrow><annotation encoding="application/x-tex">'+esc(raw)+'</annotation></semantics></math>';
      return '<span class="'+(display?'math-display':'math-inline')+'" data-math-source="'+esc(raw)+'">'+math+'</span>';
    }catch(error){
      return '<code class="math-fallback" title="公式解析失败，显示原始 TeX">'+esc(raw)+'</code>';
    }
  }

  function escapedBefore(s,i){let n=0;for(let k=i-1;k>=0&&s[k]==='\\';k--)n++;return n%2===1;}
  function endDollar(s,start,double){
    const needle=double?'$$':'$';
    for(let i=start;i<s.length;i++){
      if(s.startsWith(needle,i)&&!escapedBefore(s,i)){
        if(!double&&(s[i-1]==='$'||s[i+1]==='$'))continue;
        return i;
      }
    }return -1;
  }
  function renderText(input){
    const s=String(input??'');let out='',plain='',i=0;
    const flush=()=>{if(plain){out+=esc(plain);plain='';}};
    while(i<s.length){
      if(s[i]==='\\'&&s[i+1]==='$'){plain+='$';i+=2;continue;}
      let open='',close='',display=false,offset=0,end=-1;
      if(s.startsWith('$$',i)){open='$$';close='$$';display=true;offset=2;end=endDollar(s,i+2,true);}
      else if(s[i]==='$'&&!escapedBefore(s,i)){open='$';close='$';offset=1;end=endDollar(s,i+1,false);}
      else if(s.startsWith('\\(',i)){open='\\(';close='\\)';offset=2;end=s.indexOf(close,i+2);}
      else if(s.startsWith('\\[',i)){open='\\[';close='\\]';display=true;offset=2;end=s.indexOf(close,i+2);}
      if(open&&end>=0){
        flush();out+=renderTex(s.slice(i+offset,end),display);i=end+close.length;continue;
      }
      plain+=s[i++];
    }
    flush();return out;
  }
  function renderParagraphs(text){
    const s=String(text??'');let out='',plain='',i=0;
    const flush=()=>{if(!plain)return;out+=plain.split(/\n+/).filter(line=>line.trim()).map(line=>'<p>'+renderText(line)+'</p>').join('');plain='';};
    while(i<s.length){
      let close='',offset=0,end=-1;
      if(s.startsWith('$$',i)&&!escapedBefore(s,i)){close='$$';offset=2;end=endDollar(s,i+2,true);}
      else if(s.startsWith('\\[',i)){close='\\]';offset=2;end=s.indexOf(close,i+2);}
      if(close&&end>=0){flush();out+=renderTex(s.slice(i+offset,end),true);i=end+close.length;continue;}
      plain+=s[i++];
    }
    flush();return out;
  }

  const api={renderTex,renderText,renderParagraphs,Parser};
  global.RadarMath=api;
  if(typeof module!=='undefined')module.exports=api;
})(typeof window!=='undefined'?window:globalThis);
