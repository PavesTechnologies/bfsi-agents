import asyncio
import functools
from inspect import iscoroutinefunction

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.core.config import get_settings
from src.workflows.decision_state import LoanApplicationState

# Get the tracer initialized in your setup_telemetry

settings = get_settings()


def setup_telemetry(app):
    # Set up the tracer provider
    resource = Resource.create(attributes={SERVICE_NAME: "kyc-agent"})
    provider = TracerProvider(resource=resource)

    # In production, this would use an OTLP exporter (e.g., to Jaeger or Honeycomb)
    # For now, we export to console for verification
    if settings.env != "Development":
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317", insecure=True
        )
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Instrument FastAPI to automatically capture HTTP requests
    FastAPIInstrumentor.instrument_app(app)

def track_node(node_name: str):
    def decorator(func):
        if iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(state: LoanApplicationState, *args, **kwargs):
                tracer = trace.get_tracer("decision-agent")
                with tracer.start_as_current_span(f"node.{node_name}") as span:
                    start_time = asyncio.get_event_loop().time()
                    try:
                        result = await func(state, *args, **kwargs)
                        # Ensure result is a dict so we can add telemetry data
                        if result is None: result = {} 
                        
                        duration = asyncio.get_event_loop().time() - start_time
                        result["node_execution_times"] = {node_name: duration}
                        result["parallel_tasks_completed"] = [node_name]
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR))
                        raise
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(state: LoanApplicationState, *args, **kwargs):
                tracer = trace.get_tracer("decision-agent")
                with tracer.start_as_current_span(f"node.{node_name}") as span:
                    # Use standard time for sync nodes
                    import time
                    start_time = time.time()
                    try:
                        result = func(state, *args, **kwargs)
                        if result is None: result = {}
                        
                        duration = time.time() - start_time
                        result["node_execution_times"] = {node_name: duration}
                        result["parallel_tasks_completed"] = [node_name]
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR))
                        raise
            return sync_wrapper
    return decorator