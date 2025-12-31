FROM python:3.11-slim

WORKDIR /addon

# Install test dependencies
RUN pip install --no-cache-dir pytest pytest-cov

# Copy addon code
COPY alusteck_builder/ /addon/alusteck_builder/
COPY test_addon.py /addon/
COPY test_properties.py /addon/

# Run comprehensive test suite with better output
CMD ["python", "-u", "test_properties.py"]
