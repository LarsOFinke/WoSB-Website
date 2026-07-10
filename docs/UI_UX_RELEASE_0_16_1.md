# Release 0.16.1 — Registration separation and Build Designer cleanup

## Account and fleet lifecycle

Registration creates an account access request only. It no longer accepts or stores fleet selection,
automatic membership or a fleet application note. Extra legacy registration fields are rejected by
the API so an outdated client cannot silently reintroduce the coupling.

After an administrator approves the account, the authenticated user may open `/fleet` and submit a
separate application to the official fleet. The application remains `pending` until fleet leadership
or staff activates it.

## Squad eligibility

Squad command and roster assignments intentionally use only active memberships of the official
fleet. These users are not eligible:

- newly registered or newly approved accounts without a fleet membership;
- pending fleet applicants;
- inactive former members.

Administrators and moderators still need an active fleet membership when they are being assigned as
a squad member or squad commander; their site role grants management access, not an implicit roster
entry.

## Build Designer inventory repair

The shared inventory change handler previously passed every category through weapon validation.
Non-weapon options therefore disappeared immediately after selection because they could not be found
in the weapon catalog.

Inventory handling now:

- applies weapon arc/type checks only to weapon slot fields;
- preserves ammunition, consumables, hold cargo and Specialists;
- uses explicit item and quantity change handlers instead of mutating a `v-model` array during the
  same native change event;
- normalizes filled slots and appends exactly one empty slot while capacity remains;
- removes invalid or excess entries deterministically;
- runs a dedicated Node regression test as part of `scripts/validate.sh`.

## Deployment

This release has no database migration and requires no seed. A normal code-only update is sufficient:

```bash
sudo ./update.sh
```
