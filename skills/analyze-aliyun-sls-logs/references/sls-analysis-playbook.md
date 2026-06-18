# SLS Analysis Playbook

## Investigation Shape

Use this sequence for most production log questions:

1. Scope: region, project, logstore, time window, service, identifiers.
2. Aggregate: count, group, bucket, compare.
3. Sample: representative logs from each dominant pattern.
4. Context: preceding/following logs around one target event.
5. Cross-check: code path, deployment time, metrics, trace ID, upstream/downstream dependency.
6. Conclusion: impact, cause, confidence, next verification.

## Tool Choices

- `sls_list_projects`: discover or validate SLS projects in a region.
- `sls_list_logstores`: discover or validate logstores in a project.
- `sls_execute_sql`: execute known SLS query/SQL; use this as the default workhorse.
- `sls_log_explore`: cluster or summarize log patterns when the log field is known.
- `sls_log_compare`: compare pattern distributions across two time windows.
- `sls_get_context_logs`: inspect lines around a known log using `__pack_id__` and `__pack_meta__`.
- `sls_text_to_sql`: paid helper; use only with explicit approval or user intent.
- `sls_sop`: paid helper; use only for SLS usage/SOP questions.

## Query Patterns

Use concrete field names from the logstore when known. If field names are unknown, first sample a few logs with a narrow time window and `limit`.

Count all logs:

```sql
* | SELECT count(*) AS cnt
```

Bucket by minute:

```sql
* | SELECT date_trunc('minute', __time__) AS minute, count(*) AS cnt GROUP BY minute ORDER BY minute
```

Count by level:

```sql
* | SELECT level, count(*) AS cnt GROUP BY level ORDER BY cnt DESC
```

Top error messages or event names:

```sql
level: error | SELECT message, count(*) AS cnt GROUP BY message ORDER BY cnt DESC LIMIT 20
```

Exact identifier search:

```sql
"<identifier>" | SELECT __time__, level, message, trace_id, request_id LIMIT 50
```

Get context metadata for a target log:

```sql
"<identifier>" | with_pack_meta
```

## Alert Triage

When the user gives an alert:

1. Reconstruct the alert expression and time window if available.
2. Query the exact alert window first.
3. Query a baseline window of equal length immediately before the alert.
4. Compare by level, error class, service/container, and key identifier fields.
5. Check whether the alert is user-visible failure, retry/noise, or expected degradation logging.

## Evidence Rules

- Prefer aggregate facts over isolated examples.
- Preserve exact timestamps, region, project, logstore, and query window in the final answer.
- Do not claim root cause from a single sample unless the sample contains direct cause evidence.
- Treat missing logs as unknown until permissions, project/logstore, index, and time zone are checked.
- Do not expose AccessKey, tokens, or raw secrets from logs or local config.
