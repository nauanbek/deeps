# Monitoring Guide - DeepAgents Control Platform

This document provides a comprehensive guide to monitoring the DeepAgents Control Platform using Prometheus, Grafana, Alertmanager, and Loki.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Accessing Monitoring Tools](#accessing-monitoring-tools)
- [Understanding Dashboards](#understanding-dashboards)
- [Alert Rules](#alert-rules)
- [Custom Metrics](#custom-metrics)
- [Log Aggregation](#log-aggregation)
- [Troubleshooting](#troubleshooting)

## Overview

The DeepAgents platform uses a comprehensive monitoring stack:

- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Loki**: Log aggregation and search
- **Promtail**: Log shipping
- **Exporters**: Specialized metrics collectors (PostgreSQL, Redis, Node)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Backend    │────>│  Prometheus  │────>│   Grafana   │
│  (metrics)  │     │   (scrape)   │     │ (visualize) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           v
                    ┌──────────────┐
                    │ Alertmanager │
                    │  (notify)    │
                    └──────────────┘

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Docker    │────>│   Promtail   │────>│    Loki     │
│    Logs     │     │   (ship)     │     │  (store)    │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                                                v
                                         ┌─────────────┐
                                         │   Grafana   │
                                         │   (query)   │
                                         └─────────────┘
```

## Getting Started

### Starting the Monitoring Stack

```bash
cd infrastructure/monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Starting the Logging Stack

```bash
cd infrastructure/logging
docker-compose -f docker-compose.logging.yml up -d
```

### Verify Services

```bash
# Check monitoring services
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Check logging services
docker-compose -f logging/docker-compose.logging.yml ps
```

## Accessing Monitoring Tools

### Grafana

- **URL**: http://localhost:3000
- **Default Username**: `admin`
- **Default Password**: `admin` (change on first login)
- **Purpose**: Dashboards, visualization, alerting

**First-time Setup:**
1. Login with default credentials
2. Change password when prompted
3. Navigate to Dashboards → Browse
4. Explore pre-configured dashboards

### Prometheus

- **URL**: http://localhost:9090
- **Purpose**: Metrics storage, query interface, target status

**Useful Queries:**
```promql
# CPU usage
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory usage
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])
```

### Alertmanager

- **URL**: http://localhost:9093
- **Purpose**: Alert management, silencing, routing

**Features:**
- View active alerts
- Silence alerts temporarily
- View alert history
- Configure notification routing

### Loki (via Grafana)

- **URL**: http://localhost:3000 (Grafana → Explore → Loki datasource)
- **Purpose**: Log aggregation, search, analysis

**Example Queries:**
```logql
# All backend logs
{service="backend"}

# Error logs only
{service="backend"} |= "ERROR"

# HTTP 5xx errors
{service="backend"} |~ "5\\d{2}"

# Logs from last hour
{service="backend"} [1h]
```

## Understanding Dashboards

### System Overview Dashboard

**Purpose**: High-level system health and resource utilization

**Key Panels:**
- **CPU Usage**: Per-instance CPU utilization (warning >80%, critical >95%)
- **Memory Usage**: Available vs used memory (warning >90%, critical >95%)
- **Disk Usage**: Free space per mount point (warning <10%, critical <5%)
- **Network Traffic**: Inbound/outbound traffic rates
- **Service Health**: Up/down status of all services

**When to Use**: Daily health checks, capacity planning, incident investigation

### Application Metrics Dashboard

**Purpose**: Backend API performance and behavior

**Key Panels:**
- **Request Rate**: Requests per second by endpoint
- **Error Rate**: Percentage of 5xx and 4xx errors
- **Response Time (P95)**: 95th percentile response time
- **Active Users**: Currently active user count
- **Agent Execution Rate**: Agent runs per second by status
- **Agent Execution Duration**: P95/P50 execution times
- **Database Connections**: Active vs idle connection pool
- **Redis Connections**: Connected client count

**SLIs/SLOs:**
- Request error rate: <1% (warning), <5% (critical)
- P95 response time: <2s (target), <5s (acceptable)
- Availability: >99.9%

**When to Use**: Performance optimization, troubleshooting slow requests, capacity planning

### Database Performance Dashboard

**Purpose**: PostgreSQL health and query performance

**Key Panels:**
- **Active Connections**: Current connection count (max ~100)
- **Database Size**: Storage usage trend
- **Transactions Per Second**: Commit vs rollback rate
- **Cache Hit Ratio**: Buffer cache efficiency (target >95%)
- **Query Duration**: Slow query detection (alert >30s)
- **Deadlocks**: Locking issues
- **Rows Read vs Returned**: Index efficiency indicator
- **Database Locks**: Active locks by type

**Performance Indicators:**
- Cache hit ratio >95%: Good
- Cache hit ratio <90%: Consider increasing shared_buffers
- High rollback rate: Investigate transaction logic
- Many deadlocks: Review query patterns and locking

**When to Use**: Database optimization, query tuning, troubleshooting performance issues

## Alert Rules

### Critical Alerts (Immediate Action Required)

| Alert | Condition | Impact | Response |
|-------|-----------|--------|----------|
| BackendDown | Backend down >30s | Service unavailable | Check logs, restart service |
| PostgreSQLDown | Database down >30s | Complete service failure | Check database status, restore |
| NginxDown | Proxy down >30s | Users can't access platform | Restart nginx, check config |
| CriticalCPUUsage | CPU >95% for 2m | System unresponsive | Scale up, investigate |
| CriticalMemoryUsage | Memory >95% | Risk of OOM kill | Restart services, scale up |
| DiskSpaceCritical | Disk <5% free | Writes may fail | Clean up, expand storage |
| CriticalErrorRate | >10% 5xx errors | Service severely degraded | Check logs, rollback |

### Warning Alerts (Action Required Soon)

| Alert | Condition | Impact | Response |
|-------|-----------|--------|----------|
| HighCPUUsage | CPU >80% for 5m | Performance degraded | Monitor, plan scaling |
| HighMemoryUsage | Memory >90% | Risk of swapping | Monitor, optimize |
| DiskSpaceLow | Disk <10% free | Running out of space | Clean up soon |
| HighErrorRate | >5% 5xx errors | User experience affected | Investigate errors |
| SlowResponseTime | P95 >2s for 5m | Slow performance | Optimize queries |
| PostgreSQLTooManyConnections | >80 connections | Pool exhaustion soon | Increase pool, find leaks |

### Info Alerts (Informational)

| Alert | Condition | Impact | Response |
|-------|-----------|--------|----------|
| NoAgentExecutions | No executions for 30m | May be expected | Verify if expected |

## Custom Metrics

### Adding Application Metrics

The backend exposes metrics at `/api/v1/metrics` in Prometheus format.

**Example: Adding a custom counter**

```python
from api.v1.metrics import Counter

my_custom_counter = Counter(
    "my_custom_events_total",
    "Description of custom events",
    ["label1", "label2"],
)

# Increment counter
my_custom_counter.labels(label1="value1", label2="value2").inc()
```

**Available Metric Types:**
- **Counter**: Cumulative value that only increases
- **Gauge**: Value that can go up or down
- **Histogram**: Sample observations (duration, size)
- **Summary**: Similar to histogram with quantiles

### Adding Custom Alerts

Edit `/infrastructure/monitoring/prometheus/alerts.yml`:

```yaml
- name: custom_alerts
  interval: 30s
  rules:
    - alert: MyCustomAlert
      expr: my_custom_metric > 100
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Custom alert fired"
        description: "Custom metric exceeded threshold"
```

Reload Prometheus configuration:
```bash
docker-compose -f monitoring/docker-compose.monitoring.yml exec prometheus \
    kill -HUP 1
```

## Log Aggregation

### Viewing Logs in Grafana

1. Open Grafana → Explore
2. Select "Loki" datasource
3. Enter LogQL query
4. Adjust time range
5. View log lines

### Common LogQL Queries

```logql
# All backend logs
{service="backend"}

# Filter by log level
{service="backend"} | json | level="ERROR"

# Search for specific text
{service="backend"} |= "database error"

# Regex pattern matching
{service="backend"} |~ "user_id=[0-9]+"

# Rate of errors
rate({service="backend"} | json | level="ERROR" [5m])

# Top error messages
topk(10,
    sum by (message) (
        count_over_time({service="backend"} | json | level="ERROR" [1h])
    )
)
```

### Log Retention

- **Loki**: 30 days (configured in `loki-config.yml`)
- **Local logs**: Rotate daily, keep 10 files
- **S3 archive**: Optional long-term storage

## Troubleshooting

### Prometheus Not Scraping Targets

**Symptoms**: Missing metrics, gaps in graphs

**Diagnosis**:
1. Check Prometheus targets: http://localhost:9090/targets
2. Look for "DOWN" status
3. Check error messages

**Solutions**:
- Verify service is running: `docker-compose ps`
- Check network connectivity: `docker network inspect monitoring-network`
- Verify metrics endpoint: `curl http://backend:8000/api/v1/metrics`
- Check firewall rules

### Grafana Dashboard Shows "No Data"

**Symptoms**: Empty panels, "No data" message

**Diagnosis**:
1. Check datasource: Grafana → Configuration → Data Sources
2. Test connection
3. Verify query syntax
4. Check time range

**Solutions**:
- Ensure Prometheus is scraping: http://localhost:9090/targets
- Adjust time range to wider window
- Simplify query to test
- Check for typos in metric names

### Alerts Not Firing

**Symptoms**: Expected alerts not triggering

**Diagnosis**:
1. Check alert rules: http://localhost:9090/alerts
2. Verify alert state (Inactive, Pending, Firing)
3. Check Alertmanager: http://localhost:9093

**Solutions**:
- Verify alert rule syntax in `alerts.yml`
- Check `for` duration hasn't delayed alert
- Ensure Alertmanager is receiving alerts
- Check notification configuration

### High Memory Usage by Prometheus

**Symptoms**: Prometheus container using excessive memory

**Diagnosis**:
1. Check metrics cardinality: http://localhost:9090/tsdb-status
2. Look for high cardinality metrics

**Solutions**:
- Reduce retention time in prometheus.yml
- Drop unused metrics via relabel_configs
- Increase memory limits in docker-compose
- Archive old data to long-term storage

### Loki Not Receiving Logs

**Symptoms**: Empty log queries in Grafana

**Diagnosis**:
1. Check Promtail status: `docker-compose logs promtail`
2. Verify Loki is running: `curl http://localhost:3100/ready`
3. Check Promtail targets: `curl http://localhost:9080/targets`

**Solutions**:
- Ensure Promtail can access Docker socket
- Verify log file paths in `promtail-config.yml`
- Check Loki storage: `docker volume inspect loki_data`
- Review Promtail logs for errors

## Performance Optimization

### Reducing Query Load

- Use recording rules for expensive queries
- Increase scrape intervals for less critical metrics
- Use federated Prometheus for large deployments

### Optimizing Dashboard Performance

- Limit time ranges on heavy queries
- Use template variables to reduce panel count
- Cache dashboard JSON in CDN
- Use query result caching

### Scaling Considerations

**When to scale Prometheus:**
- Query response time >1s
- Ingestion falling behind scrape interval
- Memory usage consistently >80%

**Scaling options:**
- Increase retention period
- Add remote storage (Thanos, Cortex)
- Federate multiple Prometheus instances
- Horizontal sharding by service

## Best Practices

1. **Use labels wisely**: Don't use high-cardinality labels (user IDs, timestamps)
2. **Set meaningful alerts**: Alert on symptoms, not causes
3. **Document dashboards**: Add descriptions to panels
4. **Test alert rules**: Verify alerts fire correctly
5. **Regular cleanup**: Remove unused metrics and dashboards
6. **Monitor the monitors**: Alert on Prometheus/Grafana downtime
7. **Version control**: Keep monitoring configs in git
8. **Capacity planning**: Review trends monthly
9. **Incident reviews**: Update alerts based on incidents
10. **Team training**: Ensure team knows how to use tools

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [LogQL Documentation](https://grafana.com/docs/loki/latest/logql/)
- [Alerting Best Practices](https://prometheus.io/docs/practices/alerting/)
