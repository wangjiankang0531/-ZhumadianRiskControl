// Minimal DOM test double for state and ownership assertions, not layout/render acceptance.
class Element{
 constructor(document,tag){this.ownerDocument=document;this.tagName=tag.toUpperCase();this.children=[];this.attributes={};this.hidden=false;this.disabled=false;this._text='';this._value='';}
 set id(value){this._id=value;this.ownerDocument.ids.set(value,this);}get id(){return this._id;}
 set textContent(value){this._text=String(value);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent??String(n)).join('');}
 set value(value){this._value=String(value);}get value(){return this._value||((this.tagName==='SELECT'&&this.children[0])?this.children[0].value:'');}
 set innerHTML(_){throw Error('UNTRUSTED_HTML_NOT_ALLOWED');}
 setAttribute(k,v){this.attributes[k]=String(v);}getAttribute(k){return this.attributes[k]??null;}
 append(...nodes){for(const n of nodes){n.remove?.();n.parent=this;this.children.push(n);}}
 replaceChildren(...nodes){for(const n of this.children)n.parent=null;this.children=[];this._text='';this.append(...nodes);}
 remove(){if(this.parent){this.parent.children=this.parent.children.filter(n=>n!==this);this.parent=null;}}
}
export function documentFixture(){const document={ids:new Map(),createElement(tag){return new Element(this,tag);}};document.head=new Element(document,'head');document.viewport=new Element(document,'main');return document;}
