#!/bin/sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "usage: $0 GOOGLE_CLOUD_PROJECT [REGION]" >&2
  exit 2
fi

project_id=$1
region=${2:-asia-southeast1}
service=${AMA_CLOUD_SERVICE:-ama-cloud-01}
repository=${AMA_CLOUD_REPOSITORY:-ama-cloud}
git_sha=$(git rev-parse HEAD)
image="${region}-docker.pkg.dev/${project_id}/${repository}/${service}:${git_sha}"

test "${git_sha}" != "0bef91d77f941b3dfb5971bb46131c9e35df4f20"
gcloud config set project "${project_id}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
if ! gcloud artifacts repositories describe "${repository}" --location "${region}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${repository}" \
    --location "${region}" \
    --repository-format docker \
    --description "AMA-CLOUD-01 frozen runtime images"
fi

gcloud builds submit \
  --project "${project_id}" \
  --region "${region}" \
  --config deploy/ama-cloud/cloudbuild.yaml \
  --substitutions "_IMAGE=${image}" \
  .

gcloud run deploy "${service}" \
  --project "${project_id}" \
  --region "${region}" \
  --image "${image}" \
  --platform managed \
  --execution-environment gen2 \
  --port 8080 \
  --gpu 1 \
  --gpu-type nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --cpu 4 \
  --memory 16Gi \
  --no-cpu-throttling \
  --concurrency 1 \
  --min 0 \
  --max 1 \
  --timeout 3600 \
  --set-env-vars "AMA_DEPLOYMENT_LABEL=LIVE CLOUD RUN,AMA_RUNS_PER_MINUTE=6" \
  --allow-unauthenticated

gcloud run services describe "${service}" \
  --project "${project_id}" \
  --region "${region}" \
  --format='json(metadata.name,status.url,status.latestReadyRevisionName,spec.template.spec.containerConcurrency,spec.template.spec.timeoutSeconds,spec.template.spec.containers)'
