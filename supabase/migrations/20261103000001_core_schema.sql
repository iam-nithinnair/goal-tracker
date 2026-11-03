-- Core schema: profiles, challenges, goals, daily_entries (+ RLS, triggers)
-- See docs/03-data-model.md

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------- helpers
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- ---------------------------------------------------------------- profiles
create table public.profiles (
  id            uuid primary key references auth.users (id) on delete cascade,
  display_name  text not null default 'Challenger'
                  check (char_length(display_name) between 1 and 50),
  avatar_color  text not null default '#7c9cff',
  timezone      text not null default 'UTC',
  role          text not null default 'user' check (role in ('user', 'super_admin')),
  is_disabled   boolean not null default false,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);
create trigger profiles_updated_at before update on public.profiles
  for each row execute function public.set_updated_at();

-- A profile row is created automatically for every new auth user.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  name_guess text;
begin
  name_guess := coalesce(
    nullif(trim(new.raw_user_meta_data ->> 'display_name'), ''),
    nullif(split_part(coalesce(new.email, ''), '@', 1), ''),
    'Challenger'
  );
  insert into public.profiles (id, display_name)
  values (new.id, left(name_guess, 50))
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------- challenges
create table public.challenges (
  id           uuid primary key default gen_random_uuid(),
  owner_id     uuid references public.profiles (id) on delete cascade,
  name         text not null check (char_length(name) between 1 and 80),
  start_date   date not null,
  end_date     date not null,
  status       text not null default 'active' check (status in ('active', 'archived')),
  is_template  boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  constraint challenges_dates_ok check (end_date >= start_date),
  constraint challenges_max_length check (end_date - start_date <= 365),
  -- templates have no owner; real challenges always have one
  constraint challenges_owner_or_template check (
    (is_template and owner_id is null) or (not is_template and owner_id is not null)
  )
);
create index challenges_owner_idx on public.challenges (owner_id);
create trigger challenges_updated_at before update on public.challenges
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------- goals
create table public.goals (
  id            uuid primary key default gen_random_uuid(),
  challenge_id  uuid not null references public.challenges (id) on delete cascade,
  name          text not null check (char_length(name) between 1 and 80),
  position      integer not null default 0,
  -- A goal counts only on days between active_from and active_to (inclusive).
  active_from   date not null,
  active_to     date,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint goals_active_window_ok check (active_to is null or active_to >= active_from)
);
create index goals_challenge_position_idx on public.goals (challenge_id, position);
create trigger goals_updated_at before update on public.goals
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------- daily_entries
create table public.daily_entries (
  id          uuid primary key default gen_random_uuid(),
  goal_id     uuid not null references public.goals (id) on delete cascade,
  entry_date  date not null,
  status      text not null check (status in ('yes', 'no', 'na')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint daily_entries_goal_date_key unique (goal_id, entry_date)
);
create index daily_entries_date_idx on public.daily_entries (entry_date);
create trigger daily_entries_updated_at before update on public.daily_entries
  for each row execute function public.set_updated_at();

-- Safety net: an entry must fall inside its challenge's dates.
create or replace function public.validate_entry_date()
returns trigger
language plpgsql
as $$
declare
  c_start date;
  c_end   date;
begin
  select c.start_date, c.end_date into c_start, c_end
  from public.goals g
  join public.challenges c on c.id = g.challenge_id
  where g.id = new.goal_id;

  if new.entry_date < c_start or new.entry_date > c_end then
    raise exception 'entry_date % is outside the challenge (% to %)', new.entry_date, c_start, c_end
      using errcode = '23514';
  end if;
  return new;
end;
$$;
create trigger daily_entries_validate_date
  before insert or update of entry_date, goal_id on public.daily_entries
  for each row execute function public.validate_entry_date();

-- ---------------------------------------------------------------- Row Level Security
alter table public.profiles       enable row level security;
alter table public.challenges     enable row level security;
alter table public.goals          enable row level security;
alter table public.daily_entries  enable row level security;

-- profiles: a user reads and updates only their own row. Role/disabled flags are backend-controlled.
create policy profiles_select_own on public.profiles
  for select to authenticated using (id = auth.uid());
create policy profiles_update_own on public.profiles
  for update to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());

-- Prevent users from promoting themselves through direct table access.
create or replace function public.protect_profile_privileged_columns()
returns trigger
language plpgsql
as $$
begin
  if auth.role() = 'authenticated' then
    if new.role is distinct from old.role or new.is_disabled is distinct from old.is_disabled then
      raise exception 'role and is_disabled cannot be changed by the user' using errcode = '42501';
    end if;
  end if;
  return new;
end;
$$;
create trigger profiles_protect_privileged before update on public.profiles
  for each row execute function public.protect_profile_privileged_columns();

-- challenges: owner has full access; any signed-in user can read templates.
create policy challenges_select on public.challenges
  for select to authenticated using (owner_id = auth.uid() or is_template);
create policy challenges_insert_own on public.challenges
  for insert to authenticated with check (owner_id = auth.uid() and not is_template);
create policy challenges_update_own on public.challenges
  for update to authenticated
  using (owner_id = auth.uid() and not is_template)
  with check (owner_id = auth.uid() and not is_template);
create policy challenges_delete_own on public.challenges
  for delete to authenticated using (owner_id = auth.uid() and not is_template);

-- goals: follow ownership of the challenge; template goals are readable.
create policy goals_select on public.goals
  for select to authenticated using (
    exists (select 1 from public.challenges c
            where c.id = goals.challenge_id and (c.owner_id = auth.uid() or c.is_template))
  );
create policy goals_write_own on public.goals
  for all to authenticated
  using (exists (select 1 from public.challenges c
                 where c.id = goals.challenge_id and c.owner_id = auth.uid()))
  with check (exists (select 1 from public.challenges c
                      where c.id = goals.challenge_id and c.owner_id = auth.uid()));

-- daily_entries: owner only.
create policy entries_all_own on public.daily_entries
  for all to authenticated
  using (exists (select 1 from public.goals g
                 join public.challenges c on c.id = g.challenge_id
                 where g.id = daily_entries.goal_id and c.owner_id = auth.uid()))
  with check (exists (select 1 from public.goals g
                      join public.challenges c on c.id = g.challenge_id
                      where g.id = daily_entries.goal_id and c.owner_id = auth.uid()));

-- Anonymous callers get nothing (no policies for anon). Tables are not exposed to anon at all:
revoke all on public.profiles, public.challenges, public.goals, public.daily_entries from anon;
