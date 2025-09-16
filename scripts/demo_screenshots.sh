#!/bin/bash

# Demo screenshots script for Procurement Copilot
# This script hits API endpoints to generate demo data for marketing

set -e

BASE_URL="${BACKEND_BASE_URL:-http://localhost:8000}"
OUTPUT_DIR="./demo_data"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Generating demo data for marketing site..."

# Health check
echo "Checking API health..."
curl -s "$BASE_URL/health" | jq '.' > "$OUTPUT_DIR/health.json"

# Get tenders
echo "Fetching tenders..."
curl -s "$BASE_URL/api/v1/tenders?limit=10" | jq '.' > "$OUTPUT_DIR/tenders.json"

# Get tenders by CPV
echo "Fetching IT services tenders..."
curl -s "$BASE_URL/api/v1/tenders?cpv_codes=72000000&limit=5" | jq '.' > "$OUTPUT_DIR/it_tenders.json"

# Get construction tenders
echo "Fetching construction tenders..."
curl -s "$BASE_URL/api/v1/tenders?cpv_codes=45000000&limit=5" | jq '.' > "$OUTPUT_DIR/construction_tenders.json"

# Get consulting tenders
echo "Fetching consulting tenders..."
curl -s "$BASE_URL/api/v1/tenders?cpv_codes=79000000&limit=5" | jq '.' > "$OUTPUT_DIR/consulting_tenders.json"

# Get tenders by country
echo "Fetching French tenders..."
curl -s "$BASE_URL/api/v1/tenders?countries=FR&limit=10" | jq '.' > "$OUTPUT_DIR/french_tenders.json"

# Get tenders by value range
echo "Fetching high-value tenders..."
curl -s "$BASE_URL/api/v1/tenders?min_value=500000&limit=5" | jq '.' > "$OUTPUT_DIR/high_value_tenders.json"

# Get upcoming tenders
echo "Fetching upcoming tenders..."
curl -s "$BASE_URL/api/v1/tenders?upcoming=true&limit=10" | jq '.' > "$OUTPUT_DIR/upcoming_tenders.json"

# Get metrics
echo "Fetching metrics..."
curl -s "$BASE_URL/metrics" > "$OUTPUT_DIR/metrics.txt"

# Create a summary JSON
echo "Creating summary..."
cat > "$OUTPUT_DIR/summary.json" << EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "api_url": "$BASE_URL",
  "files": [
    "health.json",
    "tenders.json",
    "it_tenders.json",
    "construction_tenders.json",
    "consulting_tenders.json",
    "french_tenders.json",
    "high_value_tenders.json",
    "upcoming_tenders.json",
    "metrics.txt"
  ],
  "description": "Demo data for Procurement Copilot marketing site"
}
EOF

echo "Demo data generated successfully!"
echo "Files saved to: $OUTPUT_DIR"
echo ""
echo "Summary:"
ls -la "$OUTPUT_DIR"

# Optional: Create a simple HTML preview
cat > "$OUTPUT_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Procurement Copilot - Demo Data</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .file { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
        .json { background: #f5f5f5; padding: 10px; border-radius: 4px; }
        pre { overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Procurement Copilot - Demo Data</h1>
    <p>This page shows sample API responses for marketing purposes.</p>
    
    <div class="file">
        <h3>Health Check</h3>
        <div class="json">
            <pre id="health"></pre>
        </div>
    </div>
    
    <div class="file">
        <h3>Sample Tenders</h3>
        <div class="json">
            <pre id="tenders"></pre>
        </div>
    </div>
    
    <div class="file">
        <h3>IT Services Tenders</h3>
        <div class="json">
            <pre id="it-tenders"></pre>
        </div>
    </div>
    
    <script>
        // Load and display JSON files
        fetch('health.json')
            .then(response => response.json())
            .then(data => document.getElementById('health').textContent = JSON.stringify(data, null, 2));
            
        fetch('tenders.json')
            .then(response => response.json())
            .then(data => document.getElementById('tenders').textContent = JSON.stringify(data, null, 2));
            
        fetch('it_tenders.json')
            .then(response => response.json())
            .then(data => document.getElementById('it-tenders').textContent = JSON.stringify(data, null, 2));
    </script>
</body>
</html>
EOF

echo ""
echo "HTML preview created: $OUTPUT_DIR/index.html"
echo "Open in browser to view demo data"
