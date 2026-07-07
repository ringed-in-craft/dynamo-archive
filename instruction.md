Parse /app/access.log, an Apache-style access log, into a JSON summary report at /app/report.json.

The report must be a JSON object with these keys:
  - total_requests: integer, the total number of request lines in the log
  - unique_ips: integer, the number of distinct client IPs
  - top_path: string, the most frequently requested URL path (first alphabetically on a tie)

Do not modify /app/access.log.

You have 120 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
