# Sprint 3: Awards and sharing

**Goal:** stars and awards for achievements, and sharing through a public link and with friends.
**Stories:** US-15 to US-19. **Estimate:** about 14d (largest sprint; split sharing into 3b if needed). Depends on Sprint 2.

## Part A: Stars and awards

### S3-T01 Streak calculation                                      [1d]
Description: `services/streaks.py`: day streak, perfect streak, longest streak per `05-scoring-and-awards.md` (80% threshold, no-applicable-goals days neutral, today pending).
Acceptance criteria: streaks correct across N/A days, retired goals and edits to past entries.
Testing step: pytest table-driven cases incl. today pending, all-N/A day, streak broken then resumed; golden fixture has a known longest streak.

### S3-T02 Badge catalogue and storage                             [1d]
Description: `badges`, `user_badges` migration with RLS (select own; insert by backend only); seed the catalogue from doc 05.
Acceptance criteria: catalogue has all codes; unique (user, badge, challenge); clients cannot insert earned badges.
Testing step: RLS tests: user cannot insert into `user_badges`, cannot read others'; pytest for the unique constraint.

### S3-T03 Badge engine                                            [2d]
Description: `services/badges.py` evaluates rules after each entry write and returns newly earned badges; idempotent; never revokes.
Acceptance criteria: each badge in doc 05 unlocks exactly when its rule is met; writing the same entry twice earns nothing twice.
Testing step: one pytest per badge (just below and just at the threshold); idempotency test; test that editing history later does not revoke.

### S3-T04 Time-based badges job                                   [1d]
Description: scheduled job (nightly) for HALFWAY, CHALLENGE_COMPLETE, CHAMPION in each user's timezone.
Acceptance criteria: awards appear the day the condition becomes true, once.
Testing step: pytest with a frozen clock around the boundary dates and timezones; run the job twice and confirm no duplicates.

### S3-T05 Unlock toast and response contract                     [1d]
Description: entry write responses include `new_badges`; UI shows a toast/dialog with the badge and stars.
Acceptance criteria: US-15: unlock shows once, is announced to screen readers, and is dismissible.
Testing step: pytest on response shape; RTL for the toast and aria-live; Playwright: reach FIRST_PERFECT_DAY and see it.

### S3-T06 Awards page                                             [1d]
Description: earned badges (date, challenge) and locked ones with "how to earn"; filter by challenge.
Acceptance criteria: US-16: matches `GET /badges`; locked badges never show hidden rule internals beyond the description.
Testing step: RTL for earned/locked rendering; manual check with a seeded user holding several badges.

### S3-T07 Total stars                                             [0.5d]
Description: `GET /me/stars` and a stars indicator in the header.
Acceptance criteria: total equals the sum of earned badge stars, counted once per challenge.
Testing step: pytest for the sum with duplicates across challenges; RTL for the indicator.

## Part B: Sharing

### S3-T08 Public share links API                                  [1.5d]
Description: `share_links` table, create/list/revoke endpoints; token generated with `secrets` (>= 128 bits) and stored as a hash; scope `achievements` or `dashboard`; optional expiry.
Acceptance criteria: the token is returned only on creation; revoke is immediate; only the owner manages links.
Testing step: pytest: token not retrievable later, hash only in DB, another user gets 404 on list/revoke; RLS: anon cannot read the table.

### S3-T09 Public share page                                       [1.5d]
Description: `GET /public/share/{token}` and a no-login React page (card: name, dates, completion, streak, stars, badges; dashboard scope adds tables); open-graph preview tags; rate limiting.
Acceptance criteria: US-17: unknown, revoked and expired tokens all return the same 404; no email, notes or other challenges leak; page works logged out.
Testing step: pytest for the three 404 cases being indistinguishable; payload test that forbidden fields are absent; rate-limit test; Playwright in a fresh browser context.

### S3-T10 Share link management UI                                [1d]
Description: create link (scope, expiry), copy button, list with revoke, native share sheet on mobile.
Acceptance criteria: copy works; revoked link stops working on refresh of the public page.
Testing step: RTL for the dialog; Playwright: create, open link in a new context, revoke, reload, see not-found.

### S3-T11 Friend requests API                                     [1.5d]
Description: `friendships` migration + RLS; send by email, accept, decline, remove; no account enumeration.
Acceptance criteria: US-18: request to an unknown email returns the same response as to a known one; cannot friend yourself; duplicates blocked.
Testing step: pytest for each state transition and the uniform response; RLS: only requester/addressee can see a row; only addressee can accept.

### S3-T12 Friends UI                                               [1d]
Description: friends list, pending requests (accept/decline), send-by-email form, remove.
Acceptance criteria: states update without a refresh; empty state explains how to add a friend.
Testing step: RTL for list states; Playwright with two users completing a friend request.

### S3-T13 Share a challenge with a friend (API)                  [1d]
Description: `challenge_shares` migration + RLS; `POST/DELETE /challenges/{id}/shares`; only to accepted friends.
Acceptance criteria: US-19: 409 if not friends; unshare is immediate.
Testing step: pytest for friends/not friends/unshare; RLS: shared-with user can select but not write.

### S3-T14 Shared-with-me view                                      [1d]
Description: list of challenges shared with me and a read-only dashboard view with the owner's name.
Acceptance criteria: friend sees dashboard and badges, no edit controls, no notes; owner's other challenges invisible.
Testing step: Playwright with two users: A shares, B sees it read-only, A unshares, B no longer sees it; pytest that write endpoints return 403/404 for B.

### S3-T15 Cascade rules                                            [0.5d]
Description: removing a friend or deleting a challenge removes its shares and revokes its links.
Acceptance criteria: no orphaned access after removal.
Testing step: pytest: remove friend, then the former friend gets 404 on shared dashboard; delete challenge, links return 404.

## Sprint test pass
- [ ] Log until FIRST_PERFECT_DAY and a 3-day streak unlock; toasts appear once; stars total updates
- [ ] Awards page shows earned/locked correctly; editing past entries does not revoke badges
- [ ] Create a public link; open it logged out; revoke it; confirm 404
- [ ] Friend request between two users; share a challenge; friend sees read-only; unshare removes access
- [ ] Security review of share endpoints: no leaked fields, uniform 404s, rate limit, tokens hashed
- [ ] Accessibility (toasts, share dialog) and mobile layout checked
