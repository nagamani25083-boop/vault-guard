create table if not exists public.kling_audio_jobs (
 id uuid primary key,
 user_id uuid not null references auth.users(id) on delete cascade,
 kind text not null check (kind in ('text','video')),
 upstream_id text,
 state text not null default 'submitting',
 message text not null default '',
 media jsonb not null default '[]',
 saved jsonb not null default '[]',
 next_poll timestamptz not null default now(),
 created_at timestamptz not null default now()
);
alter table public.kling_audio_jobs enable row level security;
revoke all on public.kling_audio_jobs from anon, authenticated;
grant select on public.kling_audio_jobs to authenticated;
drop policy if exists own_jobs on public.kling_audio_jobs;
create policy own_jobs on public.kling_audio_jobs for select to authenticated using (auth.uid() = user_id);
create unique index if not exists kling_audio_upstream_id on public.kling_audio_jobs(kind,upstream_id) where upstream_id is not null;
insert into storage.buckets(id,name,public) values('kling-audio','kling-audio',false) on conflict(id) do nothing;
-- No public Storage policies: Edge checks ownership, then issues a short-lived signed URL.
