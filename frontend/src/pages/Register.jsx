import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Register(){
  const [username,setU] = useState("");
  const [email,setE] = useState("");
  const [password,setP] = useState("");
  const [msg,setMsg] = useState("");
  const nav = useNavigate();

  const submit = async () => {
    const r = await fetch(`${import.meta.env.VITE_API_BASE.replace('/api','')}/api/auth/register/`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({username,email,password})
    });
    if(!r.ok){ setMsg(await r.text()); return; }
    setMsg("Registered! You can sign in now.");
    setTimeout(()=>nav('/login'),800);
  }

  return (
    <div className="max-w-sm mx-auto card">
      <h2 className="text-lg font-semibold mb-3">Create account</h2>
      <input className="input mb-2" placeholder="Username" value={username} onChange={e=>setU(e.target.value)} />
      <input className="input mb-2" placeholder="Email (optional)" value={email} onChange={e=>setE(e.target.value)} />
      <input className="input mb-2" placeholder="Password" type="password" value={password} onChange={e=>setP(e.target.value)} />
      {msg && <div className="text-sm text-blue-700 mb-2">{msg}</div>}
      <button className="btn btn-primary w-full" onClick={submit}>Register</button>
    </div>
  )
}
