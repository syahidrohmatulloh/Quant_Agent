
# Incident Response

## Stale Data
- Check data adapter health
- Verify market clock
- Review data quality monitor logs

## Model Unavailable
- Check model registry status
- Verify model approval status
- Review signal loop logs

## High Rejection Rate
- Review rejection reasons in dashboard
- Check data quality issues
- Verify feature runtime

## Drawdown Alert
- Review open positions
- Check portfolio exposure
- Consider manual circuit breaker

## Circuit Breaker Open
- Investigate root cause
- Fix issue
- Manually reset circuit breaker

## Database Locked
- Stop scheduler
- Check for concurrent writes
- Restart application

## Scheduler Stuck
- Check heartbeat
- Review job store
- Restart scheduler
