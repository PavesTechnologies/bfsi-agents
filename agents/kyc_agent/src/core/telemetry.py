from opentelemetry import trace 
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider 
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.core.config import get_settings
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import time
import functools
from typing import Callable
from opentelemetry import trace
from src.workflows.kyc_engine.kyc_state import KYCState

# Get the tracer initialized in your setup_telemetry
tracer = trace.get_tracer("kyc-agent")

settings = get_settings()

def setup_telemetry(app):
    # Set up the tracer provider
    resource = Resource.create(attributes={
        SERVICE_NAME: "kyc-agent" 
    })
    provider = TracerProvider(resource=resource)
    
    # In production, this would use an OTLP exporter (e.g., to Jaeger or Honeycomb)
    # For now, we export to console for verification
    if settings.env != "Development":
        otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Instrument FastAPI to automatically capture HTTP requests
    FastAPIInstrumentor.instrument_app(app)



def track_node(node_name: str):
    """
    Unified decorator for OpenTelemetry (System) and LangSmith (State/Logic).
    Aligns with PRD Section 13 (Observability & Latency).
    """
    def decorator(func: Callable[[KYCState], KYCState]):
        @functools.wraps(func)
        def wrapper(state: KYCState, *args, **kwargs) -> KYCState:
            # 1. OpenTelemetry Span (Infrastructure Tracking)
            with tracer.start_as_current_span(f"node.{node_name}") as span:
                start_time = time.time()
                
                # Add PII-safe attributes to OTel for filtering
                span.set_attribute("node.name", node_name)
                if "raw_request" in state:
                    span.set_attribute("applicant.id", state["raw_request"]["applicant_id"])

                # Execute node logic
                result = func(state, *args, **kwargs)
                
                duration = time.time() - start_time
                
                # 2. State Updates (LangSmith & Business Logic Tracking)
                # Used for LangGraph flow control and audit logs
                result["parallel_tasks_completed"] = [node_name]
                result["node_execution_times"] = {node_name: duration}
                
                # Add result to OTel span before closing
                span.set_attribute("node.duration", duration)
                
                return result
        return wrapper
    return decorator