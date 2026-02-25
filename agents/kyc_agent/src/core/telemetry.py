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
from src.workflows.kyc_engine.kyc_state import KYCState

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
        @functools.wraps(func)
        async def wrapper(state: KYCState, *args, **kwargs) -> KYCState:
            # Fetch the tracer inside the async context
            tracer = trace.get_tracer("kyc-agent")

            # start_as_current_span works with async context managers
            with tracer.start_as_current_span(f"node.{node_name}") as span:
                start_time = asyncio.get_event_loop().time()

                span.set_attribute("node.name", node_name)

                # Execute the actual node (must be awaited)
                try:
                    if iscoroutinefunction(func):
                        result = await func(state, *args, **kwargs)
                    else:
                        # If the node is sync, run it directly
                        # Note: LangGraph usually runs sync nodes in a
                        # threadpool during ainvoke
                        result = func(state, *args, **kwargs)
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR))
                    raise

                duration = asyncio.get_event_loop().time() - start_time
                span.set_attribute("node.duration", duration)

                # Update state safely for LangSmith
                result["node_execution_times"] = {node_name: duration}
                result["parallel_tasks_completed"] = [node_name]
                return result

        return wrapper

    return decorator
