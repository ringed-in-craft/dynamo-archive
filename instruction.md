Parse /app/access.log, an Apache-style access log, into a JSON summary report at /app/report.json.

The report must be a JSON object with these keys:
1. total_requests — integer, the total number of request lines in the log
2. unique_ips — integer, the number of distinct client IPs
3. top_path — string, the most frequently requested URL path

Do not modify /app/access.log.

You have 120 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
