"use client";
import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { CheckCheck, MessageCircle, Send, User } from "lucide-react";
import { fetchWithAuth } from "@/lib/api";

type Person = { id:number; name:string; role:string };
type Thread = { id:number; participants:Person[]; last_message:string|null; unread_count:number };
type Message = { id:number; thread_id:number; sender:Person; content:string; created_at:string };

export default function MessagesPage() {
  const [threads,setThreads]=useState<Thread[]>([]), [recipients,setRecipients]=useState<Person[]>([]);
  const [active,setActive]=useState<number|null>(null), [messages,setMessages]=useState<Message[]>([]), [text,setText]=useState("");
  const [connected,setConnected]=useState(false); const retry=useRef(0), activeRef=useRef<number|null>(null), bottomRef=useRef<HTMLDivElement|null>(null);
  const loadThreads=useCallback(async()=>{ const r=await fetchWithAuth("/api/v1/internal-messages/threads"); if(r.ok)setThreads(await r.json()); },[]);
  const open=useCallback(async(id:number)=>{ activeRef.current=id; setActive(id); const r=await fetchWithAuth(`/api/v1/internal-messages/threads/${id}/messages`); if(r.ok)setMessages(await r.json()); await fetchWithAuth(`/api/v1/internal-messages/threads/${id}/read`,{method:"POST"}); loadThreads(); },[loadThreads]);
  useEffect(()=>{ loadThreads(); fetchWithAuth("/api/v1/internal-messages/recipients").then(r=>r.ok?r.json():[]).then(setRecipients); },[loadThreads]);
  useEffect(()=>{ bottomRef.current?.scrollIntoView({behavior:"smooth"}); },[messages]);
  useEffect(()=>{ let ws:WebSocket|undefined,timer:number,stopped=false;
    const connect=()=>{ const token=localStorage.getItem("token"); if(!token)return; const base=(process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000").replace(/^http/,"ws"); ws=new WebSocket(`${base}/api/v1/internal-messages/ws?token=${encodeURIComponent(token)}`);
      ws.onopen=()=>{retry.current=0;setConnected(true); loadThreads(); if(activeRef.current)open(activeRef.current);};
      ws.onmessage=e=>{const event=JSON.parse(e.data); if(event.type==="message"){if(event.message.thread_id===activeRef.current)setMessages(v=>v.some(m=>m.id===event.message.id)?v:[...v,event.message]);loadThreads();}};
      ws.onclose=()=>{setConnected(false);if(!stopped){const delay=Math.min(1000*2**retry.current++,15000);timer=window.setTimeout(connect,delay);}};
    }; connect(); return()=>{stopped=true;window.clearTimeout(timer);ws?.close();}; },[loadThreads,open]);
  async function start(id:string){if(!id)return;const r=await fetchWithAuth("/api/v1/internal-messages/threads",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({recipient_id:Number(id)})});if(r.ok){const t=await r.json();await loadThreads();open(t.id);}}
  async function send(e:FormEvent){e.preventDefault();if(!active||!text.trim())return;const content=text;setText("");const r=await fetchWithAuth(`/api/v1/internal-messages/threads/${active}/messages`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({content})});if(!r.ok)setText(content);}
  const current=threads.find(t=>t.id===active);
  return <div className="mx-auto flex h-full w-full max-w-6xl gap-4 p-4 text-foreground">
    <aside className="w-80 rounded-2xl border border-border bg-surface p-3"><div className="mb-3 flex items-center justify-between"><h1 className="text-lg font-bold">Messages</h1><span className={`text-xs ${connected?"text-[var(--success-foreground)]":"text-[var(--warning)]"}`}>{connected?"Live":"Reconnecting…"}</span></div>
      <select aria-label="Start a conversation" defaultValue="" onChange={e=>{start(e.target.value);e.target.value=""}} className="mb-3 w-full rounded-lg border border-border bg-background p-2 text-sm"><option value="">New conversation…</option>{recipients.map(p=><option key={p.id} value={p.id}>{p.name} · {p.role.replace("_"," ")}</option>)}</select>
      <div className="space-y-1">{threads.map(t=>{const p=t.participants[0];return <button key={t.id} onClick={()=>open(t.id)} className={`w-full rounded-xl p-3 text-left ${active===t.id?"bg-accent text-on-accent":"hover:bg-surface-wash"}`}><div className="flex justify-between"><b>{p?.name||"Conversation"}</b>{t.unread_count>0&&<span className="rounded-full bg-accent px-2 text-xs">{t.unread_count}</span>}</div><p className="truncate text-xs opacity-70">{t.last_message||p?.role}</p></button>})}</div>
    </aside>
    <section className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border border-border bg-surface">{active?<><header className="flex items-center gap-3 border-b border-border p-4"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-sm font-bold text-on-accent">{current?.participants[0]?.name?.slice(0,1).toUpperCase()||<User size={16}/>}</div><div><div className="font-semibold">{current?.participants[0]?.name||"Conversation"}</div><div className="text-xs capitalize text-muted-foreground">{current?.participants[0]?.role.replace("_"," ")}</div></div></header>
      <div className="flex-1 space-y-5 overflow-y-auto p-4 sm:p-6">{messages.map(m=>{const other=current?.participants[0];const mine=m.sender.id!==other?.id;const initials=m.sender.name.split(" ").map(x=>x[0]).join("").slice(0,2).toUpperCase();return <div key={m.id} className={`flex w-full items-end gap-2.5 ${mine?"justify-end":"justify-start"}`}>
        {!mine&&<div className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl border border-border bg-surface-wash text-muted-foreground"><User size={14}/></div>}
        <div className={`max-w-[76%] sm:max-w-[68%] ${mine?"flex flex-col items-end":""}`}><div className={`break-words px-4 py-2.5 text-sm leading-relaxed shadow-lg ${mine?"rounded-[20px_3px_20px_20px] bg-gradient-to-br from-accent to-accent-glow text-on-accent shadow-lg":"rounded-[3px_20px_20px_20px] border border-border bg-surface-wash text-foreground"}`}><p className="whitespace-pre-wrap">{m.content}</p></div><div className={`mt-1 flex items-center gap-1 px-1 text-[10px] text-muted-foreground ${mine?"justify-end":"justify-start"}`}><time>{new Date(m.created_at).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</time>{mine&&<CheckCheck size={12} className="text-sky-400"/>}</div></div>
        {mine&&<div className="mb-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-glow text-[10px] font-bold text-on-accent">{initials}</div>}
      </div>})}<div ref={bottomRef}/></div>
      <form onSubmit={send} className="flex gap-2 border-t border-border bg-surface p-3"><input value={text} onChange={e=>setText(e.target.value)} maxLength={10000} placeholder="Write a message…" className="min-w-0 flex-1 rounded-xl border border-border bg-surface-wash px-4 py-3 text-sm outline-none transition focus:border-accent"/><button aria-label="Send message" className="flex items-center gap-2 rounded-xl bg-accent px-5 py-3 font-semibold text-on-accent transition hover:bg-accent-hover"><Send size={16}/><span className="hidden sm:inline">Send</span></button></form></>:<div className="m-auto flex flex-col items-center gap-3 text-muted-foreground"><div className="rounded-2xl bg-accent/10 p-4 text-accent-glow"><MessageCircle size={28}/></div><p>Select or start a conversation</p></div>}</section>
  </div>;
}
