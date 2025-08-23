import React, { useState } from 'react'
import { extractJD, createJob } from '../lib/api'

export default function AddJob(){
  const [url, setUrl] = useState('')
  const [jd, setJD] = useState('')
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')
  const [preview, setPreview] = useState(null)
  const [title, setTitle] = useState('')
  const [companyName, setCompanyName] = useState('')

  async function handleExtract(){
    try{
      setErr('')
      setLoading(true)
      const data = await extractJD({ url, jd_text: jd })
      console.log('extract response:', data)   // <-- see exactly what arrived
      // Ensure all keys exist
      const shaped = {
        title: data.title ?? '',
        company: data.company ?? '',
        location: data.location ?? '',
        seniority: data.seniority ?? '',
        skills: data.skills ?? [],
        must_haves: data.must_haves ?? [],
        nice_to_haves: data.nice_to_haves ?? [],
        summary: data.summary ?? ''
      }
      setPreview(shaped)
      setTitle(shaped.title)
      setCompanyName(shaped.company)
    }catch(e){
      console.error(e)
      setErr(String(e))
    }finally{
      setLoading(false)
    }
  }

  async function handleSave(){
    if (!preview) return
    try{
      setErr('')
      const payload = {
        company_name: companyName || preview.company || 'Unknown',
        title: title || preview.title || 'Untitled',
        location: preview.location || '',
        seniority: preview.seniority || '',
        url,
        jd_raw: jd,
        jd_struct: preview,
      }
      await createJob(payload)
      // ... navigate to the job or show toast
    }catch(e){
      setErr(String(e))
    }
  }

  return (
    <div className="space-y-3">
      {/* Inputs */}
      <input className="input" placeholder="https://…" value={url} onChange={e=>setUrl(e.target.value)} />
      <textarea className="input min-h-[180px]" placeholder="Paste Job Description…" value={jd} onChange={e=>setJD(e.target.value)} />

      <div className="flex gap-2">
        <button className="btn" onClick={handleExtract} disabled={loading}>
          {loading ? 'Extracting…' : 'Extract Requirements'}
        </button>
        <button className="btn btn-primary" onClick={handleSave} disabled={!preview}>
          Save Job
        </button>
      </div>
      {err && <div className="text-red-600 text-sm">{err}</div>}

      {/* Mapped fields */}
      <input className="input" placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} />
      <input className="input" placeholder="Company" value={companyName} onChange={e=>setCompanyName(e.target.value)} />

      {/* Preview chips */}
      {preview && (
        <div className="grid md:grid-cols-3 gap-3">
          <div className="card">
            <div className="font-semibold mb-1">Must-haves</div>
            <ul className="list-disc list-inside text-sm">
              {(preview.must_haves.length ? preview.must_haves : ['—']).map((s,i)=> <li key={i}>{s}</li>)}
            </ul>
          </div>
          <div className="card">
            <div className="font-semibold mb-1">Skills</div>
            <ul className="list-disc list-inside text-sm">
              {(preview.skills.length ? preview.skills : ['—']).map((s,i)=> <li key={i}>{s}</li>)}
            </ul>
          </div>
          <div className="card">
            <div className="font-semibold mb-1">Nice-to-haves</div>
            <ul className="list-disc list-inside text-sm">
              {(preview.nice_to_haves.length ? preview.nice_to_haves : ['—']).map((s,i)=> <li key={i}>{s}</li>)}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
