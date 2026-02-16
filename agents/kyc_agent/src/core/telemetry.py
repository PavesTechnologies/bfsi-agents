from opentelemetry import trace 
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider 
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from src.core.config import get_settings
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

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