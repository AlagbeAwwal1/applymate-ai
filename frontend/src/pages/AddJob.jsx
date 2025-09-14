import React, { useState } from 'react'
import { extractJD, createJob } from '../lib/api'

export default function AddJob(){
  const [url, setUrl] = useState('')
  const [jd, setJD] = useState('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState('')
  const [success, setSuccess] = useState('')
  const [preview, setPreview] = useState(null)
  const [title, setTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [showConfirm, setShowConfirm] = useState(false)

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
    setShowConfirm(true)
  }

  async function confirmSave(){
    if (!preview) return
    try{
      setErr('')
      setSuccess('')
      setSaving(true)
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
      setSuccess('Job saved successfully!')
      setShowConfirm(false)
      // Clear form after successful save
      setUrl('')
      setJD('')
      setPreview(null)
      setTitle('')
      setCompanyName('')
    }catch(e){
      setErr(String(e))
      setShowConfirm(false)
    }finally{
      setSaving(false)
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
        <button className="btn btn-primary" onClick={handleSave} disabled={!preview || saving}>
          {saving ? 'Saving…' : 'Save Job'}
        </button>
      </div>
      {err && <div className="text-red-600 text-sm">{err}</div>}
      {success && <div className="text-green-600 text-sm">{success}</div>}

      {/* Mapped fields */}
      <input className="input" placeholder="Title" value={title} onChange={e=>setTitle(e.target.value)} />
      <input className="input" placeholder="Company" value={companyName} onChange={e=>setCompanyName(e.target.value)} />

      {/* Preview chips */}
      {preview && (
        <div className="grid md:grid-cols-3 gap-3">
          <div className="card">
            <div className="font-semibold mb-1">Must-haves</div>
            <ul className="list-disc list-inside text-sm">
              {(preview.must_haves.length ? preview.must_haves : ['—']).map((s,i)=> <li key={`must-${i}-${s.slice(0,10)}`}>{s}</li>)}
            </ul>
          </div>
          <div className="card">
            <div className="font-semibold mb-1">Skills</div>
            <ul className="list-disc list-inside text-sm">
              {(preview.skills.length ? preview.skills : ['—']).map((s,i)=> <li key={`skill-${i}-${s.slice(0,10)}`}>{s}</li>)}
            </ul>
          </div>
          <div className="card">
            <div className="font-semibold mb-1">Nice-to-haves</div>
            <ul className="list-disc list-inside text-sm">
              {(preview.nice_to_haves.length ? preview.nice_to_haves : ['—']).map((s,i)=> <li key={`nice-${s.slice(0,20)}-${i}`}>{s}</li>)}
            </ul>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-3">Confirm Save</h3>
            <p className="text-sm text-gray-600 mb-4">
              Are you sure you want to save this job?
            </p>
            <div className="text-xs text-gray-500 mb-4">
              <strong>Title:</strong> {title || preview?.title || 'Untitled'}<br/>
              <strong>Company:</strong> {companyName || preview?.company || 'Unknown'}
            </div>
            <div className="flex gap-2 justify-end">
              <button 
                className="btn" 
                onClick={() => setShowConfirm(false)}
                disabled={saving}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={confirmSave}
                disabled={saving}
              >
                {saving ? 'Saving…' : 'Save Job'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
