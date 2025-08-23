import React from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { isAuthed, clearToken } from './lib/auth'

const NavItem = ({to, children}) => (
  <NavLink to={to} className={({isActive}) => `px-3 py-2 rounded-xl ${isActive ? 'bg-gray-900 text-white' : 'hover:bg-gray-100'}`}>
    {children}
  </NavLink>
)

export default function App(){
  const nav = useNavigate();
  const authed = isAuthed();
  return (
    <div className="max-w-6xl mx-auto p-4">
      <header className="flex items-center justify-between py-3">
        <div className="text-xl font-bold">ApplyMate <span className="text-blue-600">AI</span></div>
        <nav className="flex gap-2 items-center">
          {authed && <>
            <NavItem to="/">Dashboard</NavItem>
            <NavItem to="/add">Add Job</NavItem>
            <NavItem to="/applications">Applications</NavItem>
            <NavItem to="/settings">Settings</NavItem>
          </>}
          {!authed && <>
            <NavItem to="/login">Login</NavItem>
            <NavItem to="/register">Register</NavItem>
          </>}
          {authed && <button className="btn" onClick={()=>{ clearToken(); nav('/login'); }}>Logout</button>}
        </nav>
      </header>
      <main className="mt-4">
        <Outlet />
      </main>
    </div>
  )
}
