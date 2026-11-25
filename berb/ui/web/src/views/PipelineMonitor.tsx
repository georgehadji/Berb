import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, CheckCircle2, AlertCircle, Loader2, Pause } from 'lucide-react';

// SF-25: this view used to render a hard-coded run (stage 7 at 78%, invented
// costs, papers and hypotheses) for every id. It now polls the run-status read
// model, GET /api/runs/{id}/status, and shows only what that reports.

interface RunStatusView {
  run_id: string;
  status: string;
  is_live: boolean;
  current_stage: number | null;
  current_stage_name: string;
  stage_statuses: Record<string, string>;
  topic: string;
  start_time: string;
  last_error: string | null;
  pivot_count: number;
}

interface StageDef {
  number: number;
  name: string;
}

const POLL_MS = 3000;

const badge: Record<string, string> = {
  pending: 'bg-surfaceHover text-textSecondary',
  running: 'bg-accentLight text-accent',
  retrying: 'bg-accentLight text-accent',
  done: 'bg-successLight text-success',
  failed: 'bg-errorLight text-error',
  blocked_approval: 'bg-warningLight text-warning',
  paused: 'bg-warningLight text-warning',
  stopped: 'bg-surfaceHover text-textSecondary',
};

function StatusIcon({ status }: { status: string }) {
  if (status === 'done') return <CheckCircle2 className="w-5 h-5 text-success" />;
  if (status === 'running' || status === 'retrying')
    return <Loader2 className="w-5 h-5 animate-spin text-accent" />;
  if (status === 'failed') return <AlertCircle className="w-5 h-5 text-error" />;
  if (status === 'blocked_approval' || status === 'paused')
    return <Pause className="w-5 h-5 text-warning" />;
  return <div className="w-5 h-5 rounded-full bg-surfaceHover" />;
}

function Badge({ status }: { status: string }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${badge[status] ?? badge.pending}`}>
      {status.replace('_', ' ')}
    </span>
  );
}

export function PipelineMonitorView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [run, setRun] = useState<RunStatusView | null>(null);
  const [stages, setStages] = useState<StageDef[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/pipeline/stages')
      .then((r) => r.json())
      .then((body) => setStages(body.stages ?? []))
      .catch(() => setStages([]));
  }, []);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const load = () =>
      fetch(`/api/runs/${encodeURIComponent(id)}/status`)
        .then(async (r) => {
          if (!r.ok) throw new Error(r.status === 404 ? 'Run not found' : `HTTP ${r.status}`);
          return (await r.json()) as RunStatusView;
        })
        .then((view) => {
          if (!cancelled) {
            setRun(view);
            setError(null);
          }
        })
        .catch((e: Error) => {
          if (!cancelled) setError(e.message);
        });
    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [id]);

  const total = stages.length || 23;
  const done = run ? Object.values(run.stage_statuses).filter((s) => s === 'done').length : 0;
  const progress = Math.round((done / total) * 100);

  return (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-surfaceHover rounded-lg transition-colors"
          aria-label="Back"
        >
          <ChevronLeft className="w-5 h-5 text-textSecondary" />
        </button>
        <div>
          <h1 className="text-2xl font-semibold text-textPrimary">
            {run?.topic || (id ? 'Loading…' : 'No run selected')}
          </h1>
          {id && (
            <p className="text-sm text-textSecondary">
              ID: {id}
              {run?.start_time && ` • Started: ${new Date(run.start_time).toLocaleString()}`}
            </p>
          )}
        </div>
        {run && (
          <div className="ml-auto">
            <Badge status={run.status} />
          </div>
        )}
      </div>

      {error && <div className="card text-error mb-6">{error}</div>}
      {run?.status === 'blocked_approval' && (
        <div className="card text-warning mb-6">
          A gate is waiting for approval. To approve and continue, run:{' '}
          <code>berb run --resume --output artifacts/{run.run_id} --auto-approve</code>
        </div>
      )}
      {run?.last_error && run.status === 'failed' && (
        <div className="card text-error mb-6">Last error: {run.last_error}</div>
      )}

      {run && (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-9 card">
            <h2 className="text-lg font-semibold text-textPrimary mb-4">Stages</h2>
            <div className="grid grid-cols-1 gap-2">
              {stages.map((stage) => {
                const status = run.stage_statuses[String(stage.number)] ?? 'pending';
                return (
                  <div
                    key={stage.number}
                    className={`flex items-center gap-4 p-3 rounded-lg ${
                      stage.number === run.current_stage ? 'bg-accentLight/50' : ''
                    }`}
                  >
                    <span className="w-8 text-textSecondary">{stage.number}</span>
                    <span className="flex-1 font-medium text-textPrimary">{stage.name}</span>
                    <Badge status={status} />
                    <StatusIcon status={status} />
                  </div>
                );
              })}
            </div>
          </div>

          <div className="col-span-3 card text-center">
            <h2 className="text-lg font-semibold text-textPrimary mb-4">Progress</h2>
            <span className="text-2xl font-semibold text-textPrimary">{progress}%</span>
            <p className="text-sm text-textSecondary mt-2">
              {done} of {total} stages done
            </p>
            {run.pivot_count > 0 && (
              <p className="text-sm text-textSecondary mt-1">Pivots: {run.pivot_count}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
