import time
import json
import asyncio
from functools import wraps
from typing import Any, Callable, Dict
from src.core.database import AsyncSessionLocal
from src.repositories.audit_repository import AuditRepository


def build_state_summary(state: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Build a compact compliance-friendly state summary for node audit logs."""
    if not state:
        return None

    policy_metadata = state.get("policy_metadata") or {}
    version_metadata = state.get("version_metadata") or {}
    final_response = state.get("final_response_payload") or {}
    final_decision = state.get("final_decision") or {}
    decision_payload = final_response or final_decision

    triggered_reason_keys = [
        key
        for key in [
            decision_payload.get("primary_reason_key"),
            decision_payload.get("secondary_reason_key"),
        ]
        if key
    ]
    application_id = (
        state.get("application_id")
        or final_response.get("application_id")
        or (state.get("review_packet") or {}).get("application_id")
    )
    correlation_id = state.get("correlation_id") or final_response.get("correlation_id")

    return {
        "application_id": application_id,
        "correlation_id": correlation_id,
        "policy_version": policy_metadata.get("policy_version"),
        "model_version": version_metadata.get("model_version"),
        "prompt_version": version_metadata.get("prompt_version"),
        "decision": decision_payload.get("decision"),
        "risk_tier": state.get("aggregated_risk_tier") or decision_payload.get("risk_tier"),
        "risk_score": state.get("aggregated_risk_score") or decision_payload.get("risk_score"),
        "triggered_reason_keys": triggered_reason_keys,
        "parallel_tasks_completed": state.get("parallel_tasks_completed", []),
        "state_keys": sorted(state.keys()),
    }


def audit_node(agent_name: str):
    """
    Decorator to audit LangGraph node execution.
    Logs input, output, status, and execution time to the node_audit_logs table.
    """
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def wrapper(state: Dict[str, Any], *args, **kwargs):
                start_time = time.time()
                input_copy = json.loads(json.dumps(state, default=str))
                input_summary = build_state_summary(input_copy)
                application_id = state.get("application_id") or state.get("context", {}).get("application_id", "UNKNOWN")
                
                status = "SUCCESS"
                error_msg = None
                output_state = None
                output_summary = None
                
                try:
                    result = await func(state, *args, **kwargs)
                    output_state = json.loads(json.dumps(result, default=str)) if result else None
                    output_summary = build_state_summary(output_state)
                    return result
                except Exception as e:
                    status = "FAILURE"
                    error_msg = str(e)
                    raise
                finally:
                    duration = int((time.time() - start_time) * 1000)
                    async with AsyncSessionLocal() as session:
                        repo = AuditRepository(session)
                        await repo.save_node_log(
                            application_id=str(application_id),
                            agent_name=agent_name,
                            node_name=func.__name__,
                            input_summary=input_summary,
                            input_state=input_copy,
                            output_summary=output_summary,
                            output_state=output_state,
                            status=status,
                            error_message=error_msg,
                            execution_time_ms=duration
                        )
            return wrapper
        else:
            @wraps(func)
            def wrapper(state: Dict[str, Any], *args, **kwargs):
                start_time = time.time()
                input_copy = json.loads(json.dumps(state, default=str))
                input_summary = build_state_summary(input_copy)
                application_id = state.get("application_id") or state.get("context", {}).get("application_id", "UNKNOWN")
                
                status = "SUCCESS"
                error_msg = None
                output_state = None
                output_summary = None
                
                try:
                    result = func(state, *args, **kwargs)
                    output_state = json.loads(json.dumps(result, default=str)) if result else None
                    output_summary = build_state_summary(output_state)
                    return result
                except Exception as e:
                    status = "FAILURE"
                    error_msg = str(e)
                    raise
                finally:
                    duration = int((time.time() - start_time) * 1000)
                    
                    async def save_async():
                        async with AsyncSessionLocal() as session:
                            repo = AuditRepository(session)
                            await repo.save_node_log(
                                application_id=str(application_id),
                                agent_name=agent_name,
                                node_name=func.__name__,
                                input_summary=input_summary,
                                input_state=input_copy,
                                output_summary=output_summary,
                                output_state=output_state,
                                status=status,
                                error_message=error_msg,
                                execution_time_ms=duration
                            )
                    
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(save_async())
                        else:
                            loop.run_until_complete(save_async())
                    except Exception:
                        pass
                return result
            return wrapper
    return decorator
