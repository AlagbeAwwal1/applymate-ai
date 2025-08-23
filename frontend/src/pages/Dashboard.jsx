import React, { useEffect, useState } from 'react'
import { listJobs, listApps } from '../lib/api'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Dashboard(){
  const [jobs, setJobs] = useState([])
  const [apps, setApps] = useState([])

  useEffect(() => {
    listJobs().then(setJobs)
    listApps().then(setApps)
  }, [])

  const stageCounts = ['saved','applied','oa','interview','offer','rejected'].map(s => ({
    stage: s,
    count: apps.filter(a => a.stage === s).length
  }))

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="card col-span-2">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Applications by Stage</h2>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stageCounts}>
              <XAxis dataKey="stage" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card">
        <h2 className="text-lg font-semibold mb-2">Recent Jobs</h2>
        <div className="space-y-2">
          {jobs.slice(0,6).map(j => (
            <Link key={j.id} to={`/jobs/${j.id}`} className="block p-2 rounded-lg hover:bg-gray-50 border">
              <div className="font-medium">{j.title}</div>
              <div className="text-sm text-gray-500">{j.company?.name}</div>
            </Link>
          ))}
          {jobs.length === 0 && <div className="text-sm text-gray-500">No jobs yet. <Link className="text-blue-600" to="/add">Add one</Link>.</div>}
        </div>
      </div>
    </div>
  )
}
