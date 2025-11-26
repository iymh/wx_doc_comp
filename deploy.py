import os
import sys
import time
import json
from dotenv import load_dotenv
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_code_engine_sdk.code_engine_v2 import CodeEngineV2
from ibm_cloud_sdk_core import ApiException

# Load environment variables (for API Key and App runtime envs)
load_dotenv()

# Configuration Loading
CONFIG_FILE = "ce_config.json"
config = {}

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        print(f"Loaded configuration from {CONFIG_FILE}")
    except json.JSONDecodeError as e:
        print(f"Error parsing {CONFIG_FILE}: {e}")
        sys.exit(1)
else:
    print(f"Warning: {CONFIG_FILE} not found. Falling back to environment variables.")

# Extract Config
# API Key can be in JSON or Env (Env is safer/common for secrets)
API_KEY = (config.get("API_KEY") or os.getenv("API_KEY") or os.getenv("IBMCLOUD_API_KEY") or "").strip()

REGION = config.get("IBM_REGION") or os.getenv("IBM_REGION", "jp-tok")
PROJECT_ID = config.get("CE_PROJECT_ID") or os.getenv("CE_PROJECT_ID")
APP_NAME = config.get("CE_APP_NAME") or os.getenv("CE_APP_NAME", "wx-doc-comp-app")
APP_PORT = int(config.get("CE_APP_PORT") or os.getenv("CE_APP_PORT", 8000))
APP_MIN_INSTANCES = int(config.get("CE_MIN_INSTANCES") or os.getenv("CE_MIN_INSTANCES", 1))

# Build Configuration
build_config = config.get("BUILD_CONFIG", {})
GIT_REPO_URL = build_config.get("GIT_REPO_URL") or os.getenv("GIT_REPO_URL")
GIT_BRANCH = build_config.get("GIT_BRANCH") or os.getenv("GIT_BRANCH", "main")
IMAGE_URL = build_config.get("IMAGE_URL") or os.getenv("IMAGE_URL")
REGISTRY_SECRET_NAME = build_config.get("REGISTRY_SECRET_NAME") or os.getenv("REGISTRY_SECRET_NAME")
STRATEGY_SIZE = build_config.get("STRATEGY_SIZE", "medium")

if not API_KEY:
    print("Error: API_KEY is not set (check ce_config.json or .env).")
    sys.exit(1)

if not PROJECT_ID:
    print("Error: CE_PROJECT_ID is not set (check ce_config.json).")
    sys.exit(1)

if not GIT_REPO_URL or not IMAGE_URL:
    print("Error: GIT_REPO_URL and IMAGE_URL must be set (check ce_config.json).")
    sys.exit(1)

def main():
    print(f"Starting deployment to IBM Cloud Code Engine (Source Build)...")
    print(f"Region: {REGION}")
    print(f"Project ID: {PROJECT_ID}")
    print(f"Repo: {GIT_REPO_URL} ({GIT_BRANCH})")
    print(f"Target Image: {IMAGE_URL}")
    print(f"App Port: {APP_PORT}")
    print(f"Min Instances: {APP_MIN_INSTANCES}")
    print(f"Build Strategy Size: {STRATEGY_SIZE}")

    # Authenticate
    authenticator = IAMAuthenticator(API_KEY)
    ce_client = CodeEngineV2(authenticator=authenticator)
    ce_client.set_service_url(f"https://api.{REGION}.codeengine.cloud.ibm.com/v2")

    # Check for skip build flag
    skip_build = "--skip-build" in sys.argv

    if not skip_build:
        # 1. Define Build
        build_name = f"{APP_NAME}-build"
        print(f"\n[1/3] Configuring Build '{build_name}'...")
        
        try:
            # Check if build exists
            print(f"Checking if build definition '{build_name}' exists...")
            build_response = ce_client.get_build(project_id=PROJECT_ID, name=build_name)
            build_res = build_response.get_result()
            etag = build_response.get_headers().get('Etag')
            
            print(f"Build definition found: {build_res.get('name')}")
            print("Updating build definition...")
            
            # Define the patch
            build_patch = {
                'source_url': GIT_REPO_URL,
                'source_revision': GIT_BRANCH,
                'output_image': IMAGE_URL,
                'output_secret': REGISTRY_SECRET_NAME,
                'strategy_type': 'dockerfile',
                'strategy_size': STRATEGY_SIZE
            }
            
            ce_client.update_build(
                project_id=PROJECT_ID,
                name=build_name,
                if_match=etag,
                build=build_patch
            )
            print("Build definition updated.")
        except ApiException as e:
            if e.code == 404:
                print(f"Build definition '{build_name}' not found (404). Creating new build...")
                ce_client.create_build(
                    project_id=PROJECT_ID,
                    name=build_name,
                    source_url=GIT_REPO_URL,
                    source_revision=GIT_BRANCH,
                    output_image=IMAGE_URL,
                    output_secret=REGISTRY_SECRET_NAME,
                    strategy_type="dockerfile",
                    strategy_size=STRATEGY_SIZE
                )
                print("Build definition created.")
            else:
                print(f"Error checking build: {e}")
                sys.exit(1)

        # 2. Run Build
        print(f"\n[2/3] Submitting Build Run...")
        try:
            build_run = ce_client.create_build_run(
                project_id=PROJECT_ID,
                build_name=build_name
            ).get_result()
            
            build_run_name = build_run['name']
            print(f"Build Run '{build_run_name}' submitted. Waiting for completion...")
            
            # Poll for completion
            built_image_digest = None
            while True:
                status_response = ce_client.get_build_run(project_id=PROJECT_ID, name=build_run_name).get_result()
                print(f"DEBUG: Status response type: {type(status_response)}")
                
                state = 'Unknown'
                reason = 'Unknown'

                if isinstance(status_response, dict):
                    print(f"DEBUG: Status response content: {status_response}")
                    status_field = status_response.get('status')
                    if isinstance(status_field, dict):
                        state = status_field.get('condition', 'Unknown')
                        reason = status_field.get('reason', 'Unknown')
                        built_image_digest = status_field.get('output_digest')
                    elif isinstance(status_field, str):
                        state = status_field
                        reason = 'See status string'
                    else:
                        state = 'Unknown'
                        reason = f"Unexpected status field type: {type(status_field)}"
                elif isinstance(status_response, str):
                    # If the SDK returns a raw string, we might need to parse it or it might be just the status?
                    # Let's print it to be sure in the logs
                    print(f"DEBUG: Status response content: {status_response}")
                    try:
                        status_dict = json.loads(status_response)
                        if isinstance(status_dict, dict):
                            state = status_dict.get('status', {}).get('condition', 'Unknown')
                            reason = status_dict.get('status', {}).get('reason', 'Unknown')
                            built_image_digest = status_dict.get('status', {}).get('output_digest')
                    except json.JSONDecodeError:
                        state = str(status_response) # Treat the string as the state itself if not JSON
                else:
                    print(f"DEBUG: Unexpected status type: {status_response}")

                print(f"Status: {state}")
                
                if state.lower() == 'succeeded':
                    print("Build completed successfully!")
                    if built_image_digest:
                        print(f"Build Output Digest: {built_image_digest}")
                    break
                elif state.lower() in ['failed', 'false']: 
                    print(f"Build failed. Reason: {reason}")
                    sys.exit(1)
                
                time.sleep(10)
                
        except ApiException as e:
            print(f"Build run failed: {e}")
            sys.exit(1)
    else:
        print("Skipping build steps as requested.")
        # Try to find the latest successful build run to get the digest
        print("Fetching latest successful build run to determine image digest...")
        built_image_digest = None
        try:
            build_name = f"{APP_NAME}-build"
            runs_response = ce_client.list_build_runs(
                project_id=PROJECT_ID, 
                build_name=build_name, 
                limit=10
            ).get_result()
            
            runs = runs_response.get('build_runs', [])
            
            # Sort by created_at descending just in case
            runs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            for run in runs:
                # Check status string
                status = run.get('status', '').lower()
                if status == 'succeeded':
                    # Digest is in status_details
                    status_details = run.get('status_details', {})
                    built_image_digest = status_details.get('output_digest')
                    
                    if built_image_digest:
                        print(f"Found latest successful build run: {run.get('name')}")
                        print(f"Build Output Digest: {built_image_digest}")
                        break
            
            if not built_image_digest:
                print("Warning: Could not find a recent successful build run with a digest. Using 'latest' tag.")
                
        except ApiException as e:
            print(f"Warning: Failed to list build runs: {e}")
            built_image_digest = None

    # 3. Deploy App
    print(f"\n[3/3] Deploying Application '{APP_NAME}'...")
    
    # Determine Image Reference to use
    target_image_ref = IMAGE_URL
    if built_image_digest:
        # If we have a digest, append it to ensure we deploy exactly what was built
        # Format: repo/image:tag@sha256:digest
        target_image_ref = f"{IMAGE_URL}@{built_image_digest}"
        print(f"Using specific image reference with digest: {target_image_ref}")
    else:
        print(f"Using image reference: {target_image_ref}")

    # Prepare env vars
    env_vars_to_pass = {}
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if v.startswith('"') and v.endswith('"'): v = v[1:-1]
                elif v.startswith("'") and v.endswith("'"): v = v[1:-1]
                env_vars_to_pass[k] = v
    
    env_list = []
    for k, v in env_vars_to_pass.items():
        env_list.append({'name': k, 'value': v, 'type': 'literal'})

    try:
        # Check if app exists
        try:
            ce_app_response = ce_client.get_app(project_id=PROJECT_ID, name=APP_NAME)
            ce_app = ce_app_response.get_result()
            app_etag = ce_app_response.get_headers().get('Etag')
            
            print("Updating existing application...")
            
            app_patch = {
                'image_reference': target_image_ref,
                'run_env_variables': env_list,
                'image_secret': REGISTRY_SECRET_NAME,
                'image_port': APP_PORT,
                'scale_min_instances': APP_MIN_INSTANCES
            }
            
            ce_client.update_app(
                project_id=PROJECT_ID,
                name=APP_NAME,
                if_match=app_etag,
                app=app_patch
            )
        except ApiException as e:
            if e.code == 404:
                print("Creating new application...")
                ce_client.create_app(
                    project_id=PROJECT_ID,
                    name=APP_NAME,
                    image_reference=target_image_ref,
                    run_env_variables=env_list,
                    image_secret=REGISTRY_SECRET_NAME,
                    image_port=APP_PORT,
                    scale_min_instances=APP_MIN_INSTANCES
                )
            else:
                raise e
                
        print("Deployment submitted successfully!")
        
    except ApiException as e:
        print(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
