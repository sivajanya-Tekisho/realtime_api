-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Table: calls
create table public.calls (
    call_id uuid primary key default uuid_generate_v4(),
    caller_number text,
    start_time timestamptz default now(),
    end_time timestamptz,
    call_duration integer,
    language text default 'en-US',
    intent text,
    call_status text default 'active',
    summary text,
    transcript jsonb default '[]',
    created_at timestamptz default now()
);

-- Table: call_summaries
create table public.call_summaries (
    id uuid primary key default uuid_generate_v4(),
    call_id uuid references public.calls(call_id),
    summary_text text,
    created_at timestamptz default now()
);

-- RLS Policies (Optional: Only if you want to restrict access)
-- For development with anon key (if needed):
alter table public.calls enable row level security;
create policy "Enable all access for anon" on public.calls for all using (true) with check (true);

alter table public.call_summaries enable row level security;
create policy "Enable all access for anon" on public.call_summaries for all using (true) with check (true);
