# ha-parentsquare

[![CI](https://github.com/joebeeson/ha-parentsquare/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/joebeeson/ha-parentsquare/actions/workflows/ci.yml)
[![Prek](https://github.com/joebeeson/ha-parentsquare/actions/workflows/prek.yml/badge.svg?branch=master)](https://github.com/joebeeson/ha-parentsquare/actions/workflows/prek.yml)
[![HACS validation](https://github.com/joebeeson/ha-parentsquare/actions/workflows/hacs.yml/badge.svg?branch=master)](https://github.com/joebeeson/ha-parentsquare/actions/workflows/hacs.yml)
[![CodeQL](https://github.com/joebeeson/ha-parentsquare/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/joebeeson/ha-parentsquare/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/joebeeson/ha-parentsquare/badge)](https://securityscorecards.dev/viewer/?uri=github.com/joebeeson/ha-parentsquare)
[![Latest release](https://img.shields.io/github/v/release/joebeeson/ha-parentsquare?sort=semver)](https://github.com/joebeeson/ha-parentsquare/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Home Assistant integration for the unofficial, read-only ParentSquare client.

This integration reads ParentSquare's authenticated parent web experience via
the versioned [`parentsquare-client`](https://github.com/joebeeson/parentsquare-client)
library. ParentSquare does not publish a parent-facing API, so this may stop
working when the service changes. It is not affiliated with or endorsed by
ParentSquare, Inc. Review ParentSquare's current terms and your district's
policies before installing it.

## What it provides

- one combined ParentSquare calendar with available school events, plus an
  individually selectable calendar for each discovered school;
- school and group feed polling, with group feeds selected by default and
  controllable from the integration options;
- a `ParentSquare new post` event entity with a small, automation-safe payload;
- sensors for the latest post title, recent post count, and a bounded recent
  post feed containing source links and short excerpts;
- source-specific latest/count sensors for each selected school and group, so
  automations can target one source without parsing post text;
- parent-visible students are tracked by stable ID, and discovered groups keep
  the IDs of linked students when ParentSquare supplies that relationship;
- config-flow login with a six-digit MFA step when ParentSquare requires it;
- automatic reauthentication when the ParentSquare session expires.

Post bodies, attachments, conversations, forms, sign-ups, replies,
acknowledgements, and action extraction are intentionally not exposed in this
first release. The integration stores the ParentSquare password in the Home
Assistant config entry so sessions can be renewed without manual intervention.
Home Assistant protects config-entry data; use the integration only on an
instance you trust.

## Installation

For development, copy `custom_components/parentsquare` into the Home Assistant
`config/custom_components` directory. You can open this repository directly in
HACS with the [HACS install link](https://my.home-assistant.io/redirect/hacs_repository/?owner=joebeeson&repository=ha-parentsquare&category=integration),
or add `joebeeson/ha-parentsquare` as a custom Integration repository until it
is accepted by the community catalog.
Restart Home Assistant, then add **ParentSquare** from Settings → Devices &
services.

After setup, open the ParentSquare integration's **Configure** action to choose
which schools are included, whether to keep the combined calendar, and which
group feeds should be polled. Group choices include the linked student names
when ParentSquare provides that association. School calendars are filtered by
ParentSquare's stable school identifiers. Group feeds currently contribute
posts; ParentSquare does not expose a verified group-specific calendar endpoint
in this release, so they are not presented as calendars.

The `sensor.recent_posts` entity is intended as the central dashboard feed. Its
`posts` attribute is bounded to the most recent 20 records and includes title,
timestamp, source URL, school/group IDs and names, and a short excerpt. A
Markdown card can make those source URLs clickable:

```yaml
type: markdown
title: ParentSquare
content: |
  {% set posts = state_attr('sensor.recent_posts', 'posts') or [] %}
  {% if not posts %}
  No recent posts.
  {% else %}
  {% for post in posts %}
  - [{{ post.title }}]({{ post.source_url }}) · {{ post.school_name }}{% if post.group_name %} · {{ post.group_name }}{% endif %}
  {% endfor %}
  {% endif %}
```

Templates can filter the same records by stable source ID, for example with
`selectattr('school_id', 'equalto', 12345)` or
`selectattr('group_id', 'equalto', 67890)`. The IDs are the source's IDs and
are not inferred from a child's name or from post prose.

The current repository release pins the shared client to its `v0.2.3` tag.

## Privacy and removal

The integration makes cloud requests on a roughly 15-minute schedule. It keeps
only a bounded set of post IDs for duplicate suppression and sends no writes to
ParentSquare. Remove the config entry to stop polling and remove the custom
component directory after the entry is deleted. Do not include real posts,
cookies, credentials, or private calendar URLs in bug reports; use synthetic
fixtures instead.

## Development

Run the test and quality commands from the repository root. The CI job uses
Home Assistant's current Python runtime (3.14.2) and exercises the integration
against the pinned Home Assistant release. Tagged releases package the HACS
component and publish it as a GitHub release artifact.

See [docs/releasing.md](docs/releasing.md) for the tag and HACS artifact flow.
