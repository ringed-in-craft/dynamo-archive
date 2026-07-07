Parse /app/access.log, an Apache-style access log, and write a JSON summary report to /app/report.json.

Success criteria:

1. /app/report.json contains key "total_requests" (integer) — the total number of request lines in the log.
2. /app/report.json contains key "unique_ips" (integer) — the number of distinct client IPs.
3. /app/report.json contains key "top_path" (string) — the most frequently requested URL path.
4. /app/access.log is not modified.

You have 120 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
