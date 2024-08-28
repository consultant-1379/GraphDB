#!/bin/bash
echo "Beginning service-migration"
api_server_url="https://kubernetes.default.svc"

bearer_token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
namespace=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
cacert="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"

for service_name in "$@"; do
  echo "Beginning fetch for $service_name"
  response=$(curl --silent --connect-timeout 20 --cacert $cacert -X GET \
    "${api_server_url}/api/v1/namespaces/${namespace}/services/${service_name}" \
    -H "Authorization: Bearer ${bearer_token}")

  if [[ -z "$response" ]]; then
    echo "Failed fetching response from Kubernetes API, exiting with an error code of 1..."
    exit 1
  fi

  response_code=$(echo $response | grep -oP '"code": \K\d+')

  if [ $response_code ] && [ $response_code -eq 404 ]; then
    echo "Service Resource ${service_name} doesn't exist, no need to migrate. Exiting..."
    exit 0
  fi

  cluster_ip=$(echo $response | grep -Po '"clusterIP":.*?[^\\]",' | awk -F ':' '{print $2}' | tr -d '",')

  if [ $cluster_ip == "None" ]; then
    echo "Service ${service_name} has a clusterIP of None, not deleting"
  else
    echo "Service ${service_name} has a clusterIP, deleting"
    curl --cacert $cacert -X DELETE \
      "${api_server_url}/api/v1/namespaces/${namespace}/services/${service_name}" \
      -H "Authorization: Bearer ${bearer_token}" > /dev/null 2>&1
  fi
done