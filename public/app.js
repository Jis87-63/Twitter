const key="xpanel.accounts.v1";
const get=()=>JSON.parse(localStorage.getItem(key)||"[]");
const put=items=>localStorage.setItem(key,JSON.stringify(items));
const escapeHtml=value=>String(value).replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
function render(){const items=get(),active=items.filter(item=>item.status==="ativa").length,paused=items.filter(item=>item.status==="pausada").length;document.querySelector("#total").textContent=items.length;document.querySelector("#active").textContent=active;document.querySelector("#paused").textContent=paused;document.querySelector("#updated").textContent=items.length?`${items.length} registro(s) local(is).`:"Ainda não há registros.";document.querySelector("#rows").innerHTML=items.length?items.map(item=>`<tr><td>@${escapeHtml(item.handle)}</td><td>${escapeHtml(item.owner||"—")}</td><td><span class="state ${item.status}">${escapeHtml(item.status)}</span></td><td>${new Date(item.createdAt).toLocaleString("pt-BR")}</td></tr>`).join(""):'<tr><td colspan="4" class="empty">Adicione uma conta autorizada para iniciar.</td></tr>'}
document.querySelector("#account-form").addEventListener("submit",event=>{event.preventDefault();const handle=document.querySelector("#handle").value.trim().replace(/^@/,"");if(!/^[A-Za-z0-9_]+$/.test(handle))return;if(get().some(item=>item.handle.toLowerCase()===handle.toLowerCase()))return alert("Este handle já está registrado.");put([...get(),{handle,owner:document.querySelector("#owner").value.trim(),status:document.querySelector("#status").value,createdAt:new Date().toISOString()}]);event.target.reset();render()});
document.querySelector("#clear").onclick=()=>{if(confirm("Remover todos os registros deste navegador?")){localStorage.removeItem(key);render()}};
document.querySelector("#export").onclick=()=>{const blob=new Blob([JSON.stringify(get(),null,2)],{type:"application/json"}),link=Object.assign(document.createElement("a"),{href:URL.createObjectURL(blob),download:"xpanel-contas.json"});link.click();URL.revokeObjectURL(link.href)};
const example="<main>\n  <h1>Olá, Web Edit</h1>\n  <p>Esta prévia é isolada do painel.</p>\n</main>";
const editor=document.querySelector("#editor"),output=document.querySelector("#console-output");
const log=(level,message)=>{const line=`${new Date().toLocaleTimeString("pt-BR")} [${level}] ${message}`;output.textContent=`${line}\n${output.textContent}`.slice(0,6000)};
const preview=()=>{document.querySelector("#preview-frame").srcdoc=editor.value;localStorage.setItem("xpanel.webedit.v1",editor.value);log("INFO","Prévia local atualizada no sandbox.")};
editor.value=localStorage.getItem("xpanel.webedit.v1")||example;
document.querySelector("#preview").onclick=preview;
document.querySelector("#reset-editor").onclick=()=>{editor.value=example;preview()};
document.querySelector("#clear-console").onclick=()=>output.textContent="";
document.querySelector("#download-html").onclick=()=>{const blob=new Blob([editor.value],{type:"text/html"}),link=Object.assign(document.createElement("a"),{href:URL.createObjectURL(blob),download:"pagina-local.html"});link.click();URL.revokeObjectURL(link.href);log("INFO","Arquivo HTML exportado.")};
document.querySelector("#site-form").addEventListener("submit",event=>{event.preventDefault();try{const url=new URL(document.querySelector("#site-url").value);if(url.protocol!=="https:")throw Error("Somente HTTPS");document.querySelector("#site-frame").src=url.href;log("INFO",`Visualizador aberto: ${url.hostname}`)}catch{log("ERRO","Informe uma URL HTTPS válida.")}});preview();log("INFO","Console seguro iniciado.");
render();
