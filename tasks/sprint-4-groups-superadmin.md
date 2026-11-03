# Sprint 4: Groups and super admin (later release)

**Goal:** a super admin role and groups where people work on shared goals together.
**Stories:** US-20 to US-22. **Estimate:** about 14d. Start only after the MVP is released and used; revisit scope then.

## Part A: Super admin

### S4-T01 Super admin role and guards                             [1d]
Description: `profiles.role` (`user|super_admin`), `require_role('super_admin')`, RLS read policies for admins, bootstrap script to promote the first admin (never through the public API).
Acceptance criteria: normal users get 403 on `/admin/*`; role changes only via the script or by an existing admin.
Testing step: pytest for 401/403/200 per endpoint; RLS tests for admin vs user vs anon; test that a user cannot set their own role via `PATCH /me`.

### S4-T02 Admin: users                                             [1.5d]
Description: list/search users, disable/enable (`is_disabled`), view their challenge count; disabled users are blocked at the API.
Acceptance criteria: US-20: a disabled user's token is rejected even if still valid; admins cannot disable themselves.
Testing step: pytest for blocked requests after disabling; Playwright: admin disables, user's next request fails with a clear message.

### S4-T03 Admin: challenges and badge catalogue                   [1.5d]
Description: view any challenge read-only; create/edit/deactivate badges and tune rule thresholds (validated JSON schema).
Acceptance criteria: invalid rule JSON rejected; changes apply to future evaluations only.
Testing step: pytest for rule-schema validation and "future only" behaviour; RTL for the badge form.

### S4-T04 Admin audit log                                         [1d]
Description: `admin_audit_log` records every admin action; admin UI to browse it.
Acceptance criteria: each mutating admin endpoint writes one entry with actor, action, target.
Testing step: pytest that every admin mutation produces exactly one log row; the log is not writable by anyone but the backend.

## Part B: Groups

### S4-T05 Groups data model and RLS                               [1.5d]
Description: `groups`, `group_members`, `group_challenges`; `challenges.group_challenge_id`; RLS so members see group data and nothing else.
Acceptance criteria: a non-member can see nothing of a group; member sees other members' display names only.
Testing step: RLS tests for owner, member, invited, outsider, anon.

### S4-T06 Create a group                                           [0.5d]
Description: `POST /groups`, groups list and create UI; creator becomes owner.
Acceptance criteria: name 1-80 chars; creator listed as owner.
Testing step: pytest for validation and owner membership; Playwright create flow.

### S4-T07 Invite and add members                                  [1.5d]
Description: invite by email or from friends; accept/decline; remove member; leave group.
Acceptance criteria: US-21: invites to unknown emails do not reveal account existence; the owner cannot be removed or leave without transferring ownership.
Testing step: pytest for each transition and the owner rule; Playwright with three users.

### S4-T08 Roles                                                    [0.5d]
Description: owner vs member permissions; transfer ownership.
Acceptance criteria: only owners manage members and group challenges.
Testing step: pytest permission matrix (every endpoint x role).

### S4-T09 Group challenge                                         [2d]
Description: owner defines name, dates and goals; each member gets a personal clone (linked) where they log their own entries; late joiners start from the join date.
Acceptance criteria: US-22: goals edited by the owner propagate to members for future days only; members cannot edit shared goals.
Testing step: pytest: clone creation, propagation rules, late joiner; Playwright: owner creates, two members log independently.

### S4-T10 Leaderboard                                               [1.5d]
Description: ranking by completion % (tie-break: current streak, then stars); only members see it; option to hide one's own rank.
Acceptance criteria: ordering is deterministic and matches scoring rules; N/A handling identical to the personal dashboard.
Testing step: pytest ordering and tie-breaks on fixtures; test that a hidden-rank member is still counted in group totals.

### S4-T11 Group dashboard                                          [1.5d]
Description: group completion %, per-member completion, per-goal group completion, weekly chart.
Acceptance criteria: group numbers equal the aggregation of members' personal numbers; members see only aggregate and display names, never another member's individual entries unless the owner enabled that setting.
Testing step: pytest aggregation vs personal dashboards; privacy test that individual entries are not exposed by default.

## Sprint test pass
- [ ] Promote an admin via the script; admin lists, disables and re-enables a user; actions appear in the audit log
- [ ] Normal user is blocked from every admin endpoint (UI and API)
- [ ] Create a group with 3 users; run a group challenge for several days; leaderboard and group dashboard are correct
- [ ] Outsider and removed member cannot access group data
- [ ] Privacy review of group views; accessibility and mobile checks
