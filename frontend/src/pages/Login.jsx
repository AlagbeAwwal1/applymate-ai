import React, { useState } from "react";
import { login } from "../lib/api";
import { setTokens } from "../lib/auth";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState("");
  const nav = useNavigate();
  const submit = async () => {
    try {
      setErr("");
      const { access, refresh } = await login({ username, password });
      setTokens(access , refresh);
      nav("/");
    } catch (e) {
      setErr(String(e));
    }
  };

  return (
    <div className="max-w-sm mx-auto card">
      <h2 className="text-lg font-semibold mb-3">Sign in</h2>
      <input
        className="input mb-2"
        placeholder="Username"
        value={username}
        onChange={(e) => setU(e.target.value)}
      />
      <input
        className="input mb-2"
        placeholder="Password"
        type="password"
        value={password}
        onChange={(e) => setP(e.target.value)}
      />
      {err && <div className="text-sm text-red-600 mb-2">{err}</div>}
      <button className="btn btn-primary w-full" onClick={submit}>
        Sign in
      </button>
    </div>
  );
}
