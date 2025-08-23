import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  getJob,
  listResumes,
  scoreFit,
  genDoc,
  listApps,
  createApp,
} from "../lib/api";

function Tabs({ tabs, active, setActive }) {
  return (
    <div className="flex gap-2 mb-3">
      {tabs.map((t) => (
        <button
          key={t}
          onClick={() => setActive(t)}
          className={`tab ${active === t ? "tab-active" : ""}`}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

export default function JobDetail() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [active, setActive] = useState("JD");
  const [resumes, setResumes] = useState([]);
  const [resumeId, setResumeId] = useState(null);
  const [fit, setFit] = useState(null);
  const [docs, setDocs] = useState({});
  const [apps, setApps] = useState([]);

  useEffect(() => {
    getJob(id).then(setJob);
    listResumes().then((rs) => {
      setResumes(rs);
      if (rs[0]) setResumeId(rs[0].id);
    });
    listApps(id).then(setApps);
  }, [id]);

  const runFit = async () => {
    const f = await scoreFit({ job_id: Number(id), resume_id: resumeId });
    setFit(f);
  };

  const generate = async (type) => {
    const r = await genDoc({
      job_id: Number(id),
      resume_id: resumeId,
      type,
      export: true,
    });
    setDocs((d) => ({ ...d, [type]: r }));
  };

  const createApplication = async (stage = "saved") => {
    const a = await createApp({ job: Number(id), stage });
    setApps((old) => [a, ...old]);
  };

  if (!job) return <div className="card">Loading...</div>;

  const jd = job.jd_struct || {};

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">{job.title}</h2>
            <div className="text-sm text-gray-500">
              {job.company?.name} · {job.location}
            </div>
          </div>
          <div className="flex gap-2">
            <a className="btn" href={job.url} target="_blank" rel="noreferrer">
              View Posting
            </a>
            <button
              className="btn btn-primary"
              onClick={() => createApplication("applied")}
            >
              Mark Applied
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <Tabs
          tabs={["JD", "Fit", "Docs", "Timeline"]}
          active={active}
          setActive={setActive}
        />

        {active === "JD" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <div className="font-semibold mb-1">Summary</div>
              <p className="text-sm whitespace-pre-wrap">{jd.summary}</p>
            </div>
            <div>
              <div className="font-semibold mb-1">Must-haves</div>
              <ul className="list-disc pl-5 text-sm">
                {(jd.must_haves || []).map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="font-semibold mb-1">Skills</div>
              <ul className="list-disc pl-5 text-sm">
                {(jd.skills || []).map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {active === "Fit" && (
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="label">Resume:</div>
              <select
                className="input max-w-sm"
                value={resumeId || ""}
                onChange={(e) => setResumeId(Number(e.target.value))}
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.label}
                  </option>
                ))}
              </select>
              <button className="btn btn-primary" onClick={runFit}>
                Score Fit
              </button>
            </div>

            {fit && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="card">
                    <div className="text-3xl font-bold">{fit.score}</div>
                    <div className="text-sm text-gray-500">Fit Score</div>
                  </div>
                  <div className="card">
                    <div className="font-semibold">Matches</div>
                    <div className="text-sm">
                      {(fit.match || []).join(", ") || "—"}
                    </div>
                  </div>
                  <div className="card">
                    <div className="font-semibold">Gaps</div>
                    <div className="text-sm">
                      {(fit.gaps || []).join(", ") || "—"}
                    </div>
                  </div>
                </div>

                {/* Advice panel */}
                <div className="card">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold">Make it a Perfect Fit</div>
                    <div className="text-xs text-gray-500">
                      ATS-friendly suggestions
                    </div>
                  </div>

                  {/* Keywords to add */}
                  {!!fit.advice?.keywords_to_add?.length && (
                    <div className="mb-3">
                      <div className="label mb-1">
                        Quick keywords to weave in
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {fit.advice.keywords_to_add.map((k, i) => (
                          <span
                            key={i}
                            className="px-2 py-1 rounded-full bg-blue-50 border text-blue-700 text-xs"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Sample bullets */}
                  {!!fit.advice?.bullets?.length && (
                    <div className="mb-3">
                      <div className="label mb-1">Sample tailored bullets</div>
                      <div className="space-y-2">
                        {fit.advice.bullets.map((b, i) => (
                          <div
                            key={i}
                            className="p-2 border rounded-lg flex items-start justify-between gap-2"
                          >
                            <pre className="text-sm whitespace-pre-wrap flex-1">
                              {b}
                            </pre>
                            <button
                              className="btn"
                              onClick={() => navigator.clipboard.writeText(b)}
                              title="Copy bullet"
                            >
                              Copy
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Summary suggestion */}
                  {fit.advice?.summary && (
                    <div className="mb-2">
                      <div className="label mb-1">Suggested resume summary</div>
                      <div className="p-2 border rounded-lg flex items-start justify-between gap-2">
                        <pre className="text-sm whitespace-pre-wrap flex-1">
                          {fit.advice.summary}
                        </pre>
                        <button
                          className="btn"
                          onClick={() =>
                            navigator.clipboard.writeText(fit.advice.summary)
                          }
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {active === "Docs" && (
          <div className="grid md:grid-cols-2 gap-3">
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold">Tailored Bullets</div>
                <button
                  className="btn btn-primary"
                  onClick={() => generate("bullets")}
                >
                  Generate
                </button>
              </div>
              <pre className="text-sm whitespace-pre-wrap">
                {docs.bullets?.content_md}
              </pre>
              {docs.bullets?.file_url && (
                <a
                  className="btn mt-2"
                  href={docs.bullets.file_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download DOCX
                </a>
              )}
            </div>
            <div className="card">
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold">Cover Letter</div>
                <button
                  className="btn btn-primary"
                  onClick={() => generate("coverletter")}
                >
                  Generate
                </button>
              </div>
              <pre className="text-sm whitespace-pre-wrap">
                {docs.coverletter?.content_md}
              </pre>
              {docs.coverletter?.file_url && (
                <a
                  className="btn mt-2"
                  href={docs.coverletter.file_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download DOCX
                </a>
              )}
            </div>
          </div>
        )}

        {active === "Timeline" && (
          <div className="space-y-2">
            {apps.map((a) => (
              <div
                key={a.id}
                className="p-2 border rounded-lg flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">{a.stage}</div>
                  <div className="text-sm text-gray-500">{a.notes}</div>
                </div>
                <div className="text-sm">{a.applied_at || ""}</div>
              </div>
            ))}
            {apps.length === 0 && (
              <div className="text-sm text-gray-500">No activity yet.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
