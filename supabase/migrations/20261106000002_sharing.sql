-- Sprint 3 part B: public share links, friendships and per-friend challenge shares.
-- All writes go through the backend (service role); clients may only read rows that involve them.

-- ---------------------------------------------------------------- public share links
-- Only a SHA-256 hash of the token is stored; the token itself is shown once, at creation.
create table public.share_links (
  id            uuid primary key default gen_random_uuid(),
  challenge_id  uuid not null references public.challenges (id) on delete cascade,
  owner_id      uuid not null references public.profiles (id) on delete cascade,
  token_hash    text not null unique,
  scope         text not null check (scope in ('achievements', 'dashboard')),
  expires_at    timestamptz,
  revoked_at    timestamptz,
  created_at    timestamptz not null default now()
);
create index share_links_challenge_idx on public.share_links (challenge_id);

-- ---------------------------------------------------------------- friendships
-- One row per pair, whoever asked first. A declined request is simply deleted.
create table public.friendships (
  id            uuid primary key default gen_random_uuid(),
  requester_id  uuid not null references public.profiles (id) on delete cascade,
  addressee_id  uuid not null references public.profiles (id) on delete cascade,
  status        text not null default 'pending' check (status in ('pending', 'accepted')),
  created_at    timestamptz not null default now(),
  responded_at  timestamptz,
  constraint friendships_not_self check (requester_id <> addressee_id)
);
create unique index friendships_pair_idx on public.friendships (
  least(requester_id, addressee_id), greatest(requester_id, addressee_id)
);
create index friendships_addressee_idx on public.friendships (addressee_id);

-- ---------------------------------------------------------------- challenge shares
create table public.challenge_shares (
  id            uuid primary key default gen_random_uuid(),
  challenge_id  uuid not null references public.challenges (id) on delete cascade,
  owner_id      uuid not null references public.profiles (id) on delete cascade,
  friend_id     uuid not null references public.profiles (id) on delete cascade,
  created_at    timestamptz not null default now(),
  constraint challenge_shares_once unique (challenge_id, friend_id),
  constraint challenge_shares_not_self check (owner_id <> friend_id)
);
create index challenge_shares_friend_idx on public.challenge_shares (friend_id);

alter table public.share_links       enable row level security;
alter table public.friendships       enable row level security;
alter table public.challenge_shares  enable row level security;

create policy share_links_select_own on public.share_links
  for select to authenticated using (owner_id = auth.uid());
create policy friendships_select_involved on public.friendships
  for select to authenticated using (requester_id = auth.uid() or addressee_id = auth.uid());
create policy challenge_shares_select_involved on public.challenge_shares
  for select to authenticated using (owner_id = auth.uid() or friend_id = auth.uid());
-- no insert/update/delete policies: only the backend writes, after its own checks

revoke all on public.share_links, public.friendships, public.challenge_shares from anon;

-- ---------------------------------------------------------------- lookup for friend requests
-- Resolves an email to a user id for the backend only. Clients must never be able to call this
-- (it would let anyone test which emails have accounts).
create or replace function public.find_user_id_by_email(p_email text)
returns uuid
language sql
security definer
set search_path = public, auth
stable
as $$
  select id from auth.users where lower(email) = lower(p_email) limit 1;
$$;
revoke all on function public.find_user_id_by_email(text) from public, anon, authenticated;
grant execute on function public.find_user_id_by_email(text) to service_role;
