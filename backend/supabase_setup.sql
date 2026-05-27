-- Run this in Supabase SQL Editor

create table if not exists projects (
  id text primary key,
  user_id uuid references auth.users(id) on delete cascade,
  name text not null,
  api_key text unique not null,
  created_at timestamptz default now()
);

create table if not exists conversations (
  id text primary key,
  project_id text references projects(id) on delete cascade,
  session_id text,
  user_message text not null,
  agent_response text not null,
  metadata text default '{}',
  intent text,
  sentiment text,
  is_failure boolean default false,
  failure_reason text,
  analyzed boolean default false,
  created_at timestamptz default now()
);

create table if not exists insights (
  id text primary key,
  project_id text references projects(id) on delete cascade,
  type text,
  title text,
  description text,
  count int default 1,
  created_at timestamptz default now()
);

-- Row Level Security
alter table projects enable row level security;
alter table conversations enable row level security;

-- Policies: users can only see their own projects
create policy "Users see own projects" on projects
  for all using (auth.uid() = user_id);

-- Conversations: accessible via project ownership
create policy "Users see own conversations" on conversations
  for all using (
    project_id in (select id from projects where user_id = auth.uid())
  );

-- Service role bypasses RLS (for backend API)
