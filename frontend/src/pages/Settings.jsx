import React, { useEffect, useState } from 'react'
import { uploadResume, listResumes } from '../lib/api'

export default function Settings(){
  const [file, setFile] = useState(null)
  const [label, setLabel] = useState('Base Resume')
  const [resumes, setResumes] = useState([])

  useEffect(() => { listResumes().then(setResumes) }, [])

  const upload = async () => {
    if(!file) return
    const r = await uploadResume(file, label)
    setResumes([r, ...resumes])
    setFile(null)
  }

  return (
    <div className="card">
      <h2 className="text-lg font-semibold mb-3">Resume</h2>
      <div className="grid md:grid-cols-3 gap-3">
        <div className="space-y-2">
          <div className="label">Label</div>
          <input className="input" value={label} onChange={e=>setLabel(e.target.value)} />
          <div className="label">File (.docx or .pdf)</div>
          <input type="file" onChange={e=>setFile(e.target.files?.[0])} />
          <button className="btn btn-primary" onClick={upload}>Upload</button>
        </div>
        <div className="md:col-span-2">
          <div className="font-semibold mb-2">Uploaded</div>
          <div className="space-y-2">
            {resumes.map(r => (
              <div key={r.id} className="p-2 border rounded-lg">
                <div className="font-medium">{r.label}</div>
                <div className="text-xs text-gray-500">#{r.id} · {r.file}</div>
              </div>
            ))}
            {resumes.length===0 && <div className="text-sm text-gray-500">No resumes uploaded yet.</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
