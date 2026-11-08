# AI Staff Brain PoC (Mock data only)

This isolated branch and directory serve the V2 demo UI behind basic authentication. No real Drive, NAS, model API, or user data are connected. Use no internal data or credentials in this app.

Render Docker web service rootDir: ai-staff-brain-poc; dockerContext: ai-staff-brain-poc; Dockerfile: ai-staff-brain-poc/Dockerfile. Configure POC_USERNAME and POC_PASSWORD as secret environment variables. The /health endpoint is public for platform health checks. This is a temporary demo, not SSO; integrate organizational SSO and proper authorization before any internal data.
