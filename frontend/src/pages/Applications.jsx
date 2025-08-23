import React, { useEffect, useState, useMemo } from 'react'
import { listApps, listJobs, updateApp } from '../lib/api'
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd'

const STAGES = ["saved","applied","oa","interview","offer","rejected"]

export default function Applications(){
  const [apps, setApps] = useState([])
  const [jobsById, setJobsById] = useState({})

  useEffect(() => {
    listApps().then(setApps)
    listJobs().then(js => {
      const map = {}; js.forEach(j => map[j.id] = j); setJobsById(map)
    })
  }, [])

  const grouped = useMemo(() => {
    const g = {}; STAGES.forEach(s => g[s] = [])
    apps.forEach(a => g[a.stage].push(a))
    return g
  }, [apps])

  const onDragEnd = async (result) => {
    const { source, destination, draggableId } = result
    if (!destination) return
    const srcStage = source.droppableId
    const dstStage = destination.droppableId
    if (srcStage === dstStage && source.index === destination.index) return

    const appId = Number(draggableId)
    // optimistic UI
    setApps(prev => prev.map(a => a.id===appId ? {...a, stage: dstStage} : a))
    try {
      await updateApp(appId, { stage: dstStage })
    } catch (e) {
      // rollback on error
      setApps(prev => prev.map(a => a.id===appId ? {...a, stage: srcStage} : a))
      alert("Failed to move card: " + e)
    }
  }

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="grid md:grid-cols-6 gap-3">
        {STAGES.map(stage => (
          <Droppable droppableId={stage} key={stage}>
            {(provided) => (
              <div ref={provided.innerRef} {...provided.droppableProps} className="card min-h-[300px]">
                <div className="font-semibold mb-2">{stage.toUpperCase()}</div>
                {grouped[stage].map((a, idx) => (
                  <Draggable draggableId={String(a.id)} index={idx} key={a.id}>
                    {(prov) => (
                      <div ref={prov.innerRef} {...prov.draggableProps} {...prov.dragHandleProps}
                           className="p-2 mb-2 border rounded-lg bg-white">
                        <div className="text-sm font-medium">{jobsById[a.job]?.title || '—'}</div>
                        <div className="text-xs text-gray-500">{jobsById[a.job]?.company?.name || ''}</div>
                        {a.notes && <div className="text-xs mt-1">{a.notes}</div>}
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
                {grouped[stage].length===0 && <div className="text-sm text-gray-500">Drop here</div>}
              </div>
            )}
          </Droppable>
        ))}
      </div>
    </DragDropContext>
  )
}
