#!/usr/bin/env python
"""Run the Log Monitor Agent on a variety of example log messages.

This script demonstrates the agent's behavior across different log types,
including library-specific errors where the MCP research tools (DeepWiki,
Context7) can provide valuable documentation lookups.

Usage:
    python run_examples.py
"""

from log_monitor_agent import process_log_message

# 20 example log messages covering various scenarios
# Many include real library errors where documentation lookup would be helpful
EXAMPLES = [
    # === KUBERNETES PYTHON CLIENT ERRORS ===
    # These errors would benefit from looking up kubernetes-client/python docs
    "ERROR: kubernetes.client.rest.ApiException: (403) Forbidden: pods is forbidden: User 'system:serviceaccount:default:myapp' cannot list resource 'pods' in API group '' in namespace 'production'",
    "ERROR: kubernetes.client.rest.ApiException: (404) Not Found: deployments.apps 'nginx-deployment' not found in namespace 'staging'",
    "ERROR: kubernetes.client.rest.ApiException: (409) Conflict: Operation cannot be fulfilled on configmaps 'app-config': the object has been modified; please apply your changes to the latest version",
    
    # === REDIS-PY ERRORS ===
    # These errors would benefit from looking up redis/redis-py docs
    "ERROR: redis.exceptions.ConnectionError: Error 111 connecting to redis-master:6379. Connection refused.",
    "ERROR: redis.exceptions.WatchError: Watched variable changed during transaction - key 'inventory:item:12345' was modified by another client",
    "ERROR: redis.exceptions.TimeoutError: Timeout reading from redis-cluster:6379 after 30.0 seconds",
    
    # === KAFKA ERRORS ===
    # These errors would benefit from looking up apache/kafka docs
    "ERROR: kafka.errors.KafkaTimeoutError: Failed to update metadata after 60.0 secs - broker may be unreachable",
    "ERROR: kafka.errors.NotLeaderForPartitionError: This server is not the leader for topic-partition orders-events-3",
    "ERROR: org.apache.kafka.common.errors.ProducerFencedException: Producer with transactionalId 'order-processor' has been fenced by a newer producer instance",
    
    # === SQLALCHEMY / DATABASE ERRORS ===
    # These errors would benefit from looking up sqlalchemy/sqlalchemy docs
    "ERROR: sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at 'db.example.com' (10.0.1.50), port 5432 failed: Connection timed out",
    "ERROR: sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint 'users_email_key' - DETAIL: Key (email)=(user@example.com) already exists",
    "ERROR: sqlalchemy.pool.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00",
    
    # === LANGCHAIN ERRORS ===
    # These errors would benefit from looking up langchain-ai/langchain docs
    "ERROR: langchain_core.exceptions.OutputParserException: Failed to parse LLM output - expected JSON object but received malformed response",
    "ERROR: langchain.schema.InvalidToolCall: Tool 'search_database' received invalid arguments: missing required parameter 'query'",
    
    # === AWS BOTO3 ERRORS ===
    # These errors would benefit from looking up AWS boto3 docs
    "ERROR: botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the GetObject operation: Access Denied for s3://my-bucket/private/data.json",
    "ERROR: botocore.exceptions.ClientError: An error occurred (ThrottlingException) when calling the DescribeInstances operation: Rate exceeded",
    
    # === HIGH SEVERITY WARNINGS ===
    "WARNING: Memory usage at 94% on pod ml-inference-worker-7b9c4 - OOMKilled likely imminent",
    "WARNING: Certificate for *.api.example.com expires in 12 hours (NotAfter: 2024-01-15T23:59:59Z)",
    
    # === NORMAL/INFO LOGS (no action expected) ===
    "INFO: Successfully connected to PostgreSQL database at db.example.com:5432",
    "INFO: Kafka consumer group 'order-processors' rebalanced - now consuming from partitions [0, 1, 2]",
]


def main():
    """Run the agent on all example log messages."""
    print("=" * 70)
    print("LOG MONITOR AGENT - EXAMPLE RUNS")
    print("=" * 70)
    print(f"\nRunning {len(EXAMPLES)} example log messages...")
    print("Examples include library-specific errors where MCP tools")
    print("(DeepWiki, Context7) can provide documentation lookups.\n")
    
    for i, log_message in enumerate(EXAMPLES, 1):
        print(f"\n{'=' * 70}")
        print(f"EXAMPLE {i}/{len(EXAMPLES)}")
        print("=" * 70)
        print(f"Input: {log_message}")
        print("-" * 60)
        
        try:
            process_log_message(log_message)
        except Exception as e:
            print(f"ERROR running agent: {e}")
        
        print()  # Blank line between examples
    
    print("=" * 70)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
