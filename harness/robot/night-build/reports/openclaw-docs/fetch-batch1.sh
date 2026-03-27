#!/bin/bash
# Batch 1: start/ + install/ + gateway/ + nodes/ + platforms/ + vps.md
BASE="/Users/lr/.openclaw/workspace/harness/robot/night-build/reports/openclaw-docs"
mkdir -p "$BASE"/{start,install,gateway,nodes,platforms}

URLS=(
  # === start/ (13 pages) ===
  "start/bootstrapping.md|start/bootstrapping"
  "start/docs-directory.md|start/docs-directory"
  "start/getting-started.md|start/getting-started"
  "start/hubs.md|start/hubs"
  "start/lore.md|start/lore"
  "start/onboarding.md|start/onboarding"
  "start/onboarding-overview.md|start/onboarding-overview"
  "start/openclaw.md|start/openclaw"
  "start/setup.md|start/setup"
  "start/showcase.md|start/showcase"
  "start/wizard.md|start/wizard"
  "start/wizard-cli-automation.md|start/wizard-cli-automation"
  "start/wizard-cli-reference.md|start/wizard-cli-reference"
  # === install/ (23 pages) ===
  "install/index.md|install/index"
  "install/ansible.md|install/ansible"
  "install/azure.md|install/azure"
  "install/bun.md|install/bun"
  "install/development-channels.md|install/development-channels"
  "install/digitalocean.md|install/digitalocean"
  "install/docker.md|install/docker"
  "install/docker-vm-runtime.md|install/docker-vm-runtime"
  "install/exe-dev.md|install/exe-dev"
  "install/fly.md|install/fly"
  "install/gcp.md|install/gcp"
  "install/hetzner.md|install/hetzner"
  "install/installer.md|install/installer"
  "install/kubernetes.md|install/kubernetes"
  "install/macos-vm.md|install/macos-vm"
  "install/migrating.md|install/migrating"
  "install/migrating-matrix.md|install/migrating-matrix"
  "install/nix.md|install/nix"
  "install/node.md|install/node"
  "install/northflank.md|install/northflank"
  "install/oracle.md|install/oracle"
  "install/podman.md|install/podman"
  "install/railway.md|install/railway"
  "install/raspberry-pi.md|install/raspberry-pi"
  "install/render.md|install/render"
  "install/uninstall.md|install/uninstall"
  "install/updating.md|install/updating"
  # === gateway/ (31 pages) ===
  "gateway/index.md|gateway/index"
  "gateway/authentication.md|gateway/authentication"
  "gateway/background-process.md|gateway/background-process"
  "gateway/bonjour.md|gateway/bonjour"
  "gateway/bridge-protocol.md|gateway/bridge-protocol"
  "gateway/cli-backends.md|gateway/cli-backends"
  "gateway/configuration.md|gateway/configuration"
  "gateway/configuration-examples.md|gateway/configuration-examples"
  "gateway/configuration-reference.md|gateway/configuration-reference"
  "gateway/discovery.md|gateway/discovery"
  "gateway/doctor.md|gateway/doctor"
  "gateway/gateway-lock.md|gateway/gateway-lock"
  "gateway/health.md|gateway/health"
  "gateway/heartbeat.md|gateway/heartbeat"
  "gateway/local-models.md|gateway/local-models"
  "gateway/logging.md|gateway/logging"
  "gateway/multiple-gateways.md|gateway/multiple-gateways"
  "gateway/network-model.md|gateway/network-model"
  "gateway/openai-http-api.md|gateway/openai-http-api"
  "gateway/openresponses-http-api.md|gateway/openresponses-http-api"
  "gateway/openshell.md|gateway/openshell"
  "gateway/pairing.md|gateway/pairing"
  "gateway/protocol.md|gateway/protocol"
  "gateway/remote.md|gateway/remote"
  "gateway/remote-gateway-readme.md|gateway/remote-gateway-readme"
  "gateway/sandbox-vs-tool-policy-vs-elevated.md|gateway/sandbox-vs-tool-policy-vs-elevated"
  "gateway/sandboxing.md|gateway/sandboxing"
  "gateway/secrets.md|gateway/secrets"
  "gateway/secrets-plan-contract.md|gateway/secrets-plan-contract"
  "gateway/security/index.md|gateway/security"
  "gateway/tailscale.md|gateway/tailscale"
  "gateway/tools-invoke-http-api.md|gateway/tools-invoke-http-api"
  "gateway/troubleshooting.md|gateway/troubleshooting"
  "gateway/trusted-proxy-auth.md|gateway/trusted-proxy-auth"
  # === nodes/ (10 pages) ===
  "nodes/index.md|nodes/index"
  "nodes/audio.md|nodes/audio"
  "nodes/camera.md|nodes/camera"
  "nodes/images.md|nodes/images"
  "nodes/location-command.md|nodes/location-command"
  "nodes/media-understanding.md|nodes/media-understanding"
  "nodes/talk.md|nodes/talk"
  "nodes/troubleshooting.md|nodes/troubleshooting"
  "nodes/voicewake.md|nodes/voicewake"
  # === platforms/ (25 pages) ===
  "platforms/index.md|platforms/index"
  "platforms/android.md|platforms/android"
  "platforms/ios.md|platforms/ios"
  "platforms/linux.md|platforms/linux"
  "platforms/macos.md|platforms/macos"
  "platforms/windows.md|platforms/windows"
  "platforms/mac/bundled-gateway.md|platforms/mac/bundled-gateway"
  "platforms/mac/canvas.md|platforms/mac/canvas"
  "platforms/mac/child-process.md|platforms/mac/child-process"
  "platforms/mac/dev-setup.md|platforms/mac/dev-setup"
  "platforms/mac/health.md|platforms/mac/health"
  "platforms/mac/icon.md|platforms/mac/icon"
  "platforms/mac/logging.md|platforms/mac/logging"
  "platforms/mac/menu-bar.md|platforms/mac/menu-bar"
  "platforms/mac/peekaboo.md|platforms/mac/peekaboo"
  "platforms/mac/permissions.md|platforms/mac/permissions"
  "platforms/mac/remote.md|platforms/mac/remote"
  "platforms/mac/signing.md|platforms/mac/signing"
  "platforms/mac/skills.md|platforms/mac/skills"
  "platforms/mac/voice-overlay.md|platforms/mac/voice-overlay"
  "platforms/mac/voicewake.md|platforms/mac/voicewake"
  "platforms/mac/webchat.md|platforms/mac/webchat"
  "platforms/mac/xpc.md|platforms/mac/xpc"
  # === vps.md (1 page) ===
  "vps.md|vps"
)

TOTAL=${#URLS[@]}
echo "Total URLs to fetch: $TOTAL"

for i in "${!URLS[@]}"; do
  entry="${URLS[$i]}"
  url_path="${entry%%|*}"
  file_rel="${entry##*|}"
  
  # Determine category directory
  category="${file_rel%/*}"
  filename="${file_rel##*/}"
  outdir="$BASE/$category"
  outfile="$outdir/${filename}.md"
  
  url="https://docs.openclaw.ai/$url_path"
  
  # Skip if file already exists with size > 500 bytes
  if [ -f "$outfile" ] && [ $(stat -f%z "$outfile" 2>/dev/null || stat -c%s "$outfile" 2>/dev/null || echo 0) -gt 500 ]; then
    echo "[$((i+1))/$TOTAL] SKIP (exists): $url_path"
    continue
  fi
  
  echo "[$((i+1))/$TOTAL] FETCH: $url_path"
  
  # Fetch with curl and extract content
  content=$(curl -sL "$url" -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
    -H "Accept: text/markdown,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
    -H "Accept-Language: en-US,en;q=0.9" \
    --max-time 30 2>&1)
  
  status=$?
  
  if [ $status -ne 0 ] || [ -z "$content" ]; then
    echo "  -> FAILED (curl exit: $status)"
    continue
  fi
  
  # Check for error pages (very short content or obvious error indicators)
  content_len=${#content}
  
  if [ $content_len -lt 200 ]; then
    echo "  -> FAILED (content too short: $content_len bytes)"
    continue
  fi
  
  # Write to file
  echo "$content" > "$outfile"
  actual_size=$(wc -c < "$outfile")
  echo "  -> OK ($actual_size bytes) -> $outfile"
  
  # Small delay to be nice to the server
  sleep 0.3
done

echo ""
echo "=== FETCH COMPLETE ==="
echo ""
echo "File sizes summary:"
for dir in start install gateway nodes platforms; do
  count=$(ls "$BASE/$dir"/*.md 2>/dev/null | wc -l | tr -d ' ')
  total_size=$(cat "$BASE/$dir"/*.md 2>/dev/null | wc -c)
  echo "  $dir/: $count files, $total_size bytes"
done
