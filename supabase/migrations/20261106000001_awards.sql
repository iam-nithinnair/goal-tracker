-- Sprint 3 part A: badge catalogue and earned badges (docs/05-scoring-and-awards.md).
-- Clients can only READ their own earned badges; the backend (service role) is the only writer.

create table public.badges (
  code         text primary key,
  name         text not null,
  description  text not null,
  stars        int  not null check (stars > 0),
  sort_order   int  not null,
  is_active    boolean not null default true,
  -- tunable thresholds for the badge engine; an admin edits this in Sprint 4
  rule         jsonb not null default '{}'::jsonb
);

create table public.user_badges (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references public.profiles (id) on delete cascade,
  badge_code    text not null references public.badges (code),
  challenge_id  uuid not null references public.challenges (id) on delete cascade,
  earned_on     date not null,
  created_at    timestamptz not null default now(),
  constraint user_badges_once unique (user_id, badge_code, challenge_id)
);
create index user_badges_user_idx on public.user_badges (user_id);

alter table public.badges      enable row level security;
alter table public.user_badges enable row level security;

create policy badges_read on public.badges
  for select to authenticated using (is_active);
create policy user_badges_select_own on public.user_badges
  for select to authenticated using (user_id = auth.uid());
-- no insert/update/delete policies: only the service role can award a badge

revoke all on public.badges, public.user_badges from anon;

insert into public.badges (code, name, description, stars, sort_order, rule) values
  ('FIRST_LOG',          'First check-in',     'Log your first goal.',                                           1, 10,  '{}'),
  ('FIRST_PERFECT_DAY',  'Perfect day',        'Complete every goal that applies in a single day.',              2, 20,  '{}'),
  ('STREAK_3',           'Warm-up',            'Score 80% or more for 3 days in a row.',                         1, 30,  '{"days": 3}'),
  ('STREAK_7',           'One week strong',    'Score 80% or more for 7 days in a row.',                         3, 40,  '{"days": 7}'),
  ('STREAK_14',          'Two weeks strong',   'Score 80% or more for 14 days in a row.',                        5, 50,  '{"days": 14}'),
  ('STREAK_30',          'Month of habit',     'Score 80% or more for 30 days in a row.',                       10, 60,  '{"days": 30}'),
  ('WEEK_80',            'Solid week',         'Finish a full week with 80% or more of your goals done.',        2, 70,  '{"completion": 0.8}'),
  ('MONTH_80',           'Solid month',        'Finish a calendar month with 80% or more of your goals done.',   5, 80,  '{"completion": 0.8}'),
  ('GOAL_MASTER',        'Goal master',        'Reach 90% on a single goal over at least 14 days.',              3, 90,  '{"completion": 0.9, "min_days": 14}'),
  ('COMEBACK',           'Comeback',           'Score 80% or more right after 3 or more days below 50%.',        2, 100, '{"low_days": 3}'),
  ('HALFWAY',            'Halfway there',      'Reach the midpoint of your challenge.',                          2, 110, '{}'),
  ('CHALLENGE_COMPLETE', 'Challenge complete', 'Finish a challenge with 60% or more of your goals done.',        10, 120, '{"completion": 0.6}'),
  ('CHALLENGE_CHAMPION', 'Champion',           'Finish a challenge with 90% or more of your goals done.',       20, 130, '{"completion": 0.9}')
on conflict (code) do nothing;
