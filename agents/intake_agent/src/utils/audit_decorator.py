import time
import json
import asyncio
from functools import wraps
from typing import Any, Callable, Dict
from src.core.database import AsyncSessionLocal
from src.repositories.audit_repository import AuditRepository

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
                # Deep copy input state for logging
                input_copy = json.loads(json.dumps(state, default=str))
                application_id = state.get("application_id") or state.get("context", {}).get("application_id", "UNKNOWN")
                
                status = "SUCCESS"
                error_msg = None
                output_state = None
                
                try:
                    result = await func(state, *args, **kwargs)
                    output_state = json.loads(json.dumps(result, default=str)) if result else None
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
                            input_state=input_copy,
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
                application_id = state.get("application_id") or state.get("context", {}).get("application_id", "UNKNOWN")
                
                status = "SUCCESS"
                error_msg = None
                output_state = None
                
                try:
                    result = func(state, *args, **kwargs)
                    output_state = json.loads(json.dumps(result, default=str)) if result else None
                    return result
                except Exception as e:
                    status = "FAILURE"
                    error_msg = str(e)
                    raise
                finally:
                    duration = int((time.time() - start_time) * 1000)
                    
                    # For sync nodes, we still need to run the async save. 
                    # This might be tricky in some environments, but LangGraph nodes are usually awaitable if called in an async graph.
                    # Or we can use a background task.
                    async def save_async():
                        async with AsyncSessionLocal() as session:
                            repo = AuditRepository(session)
                            await repo.save_node_log(
                                application_id=str(application_id),
                                agent_name=agent_name,
                                node_name=func.__name__,
                                input_state=input_copy,
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
                        # Fallback for complex threading/event loop cases
                        pass
            return wrapper
    return decorator
