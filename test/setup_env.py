#!/usr/bin/env python3

'''
We use it to install the GraphDB helm chart.
'''

import os
import helm3procs
import utilprocs

NAMESPACE = os.environ['kubernetes_namespace']
HELM_REPO = os.environ['helm_repo']
CHART_NAME = os.environ['baseline_chart_name']
BASELINE_CHART_VERSION = os.environ['baseline_chart_version']


def helm_deploy_chart(name, repo, version, options, timeout=None, wait=True):
    release_name = f'{name}-{NAMESPACE}'[:53]
    repo_name = f'{name}-repo'

    helm3procs.add_helm_repo(repo, repo_name)
    helm3procs.helm_get_chart_from_repo(name, version, repo_name)
    helm3procs.helm_install_chart_from_repo_with_dict(
        name,
        release_name,
        NAMESPACE,
        helm_repo_name=repo_name,
        chart_version=version,
        settings_dict=options,
        timeout=timeout,
        should_wait=wait)


def deploy_bro():
    bro_version = os.environ['bro-version']
    bro_helm_repo = os.environ['bro-helm-repo']
    bro_chart_name = os.environ['bro-chart-name']

    options = {"security.tls.broToAgent.enabled": "false", "bro.enableAgentDiscovery": "true", "global.security.tls.enabled": "false"}

    utilprocs.log("Deplying BRO")
    helm_deploy_chart(
        bro_chart_name,
        bro_helm_repo,
        bro_version,
        options,
        timeout=600,
        wait=True)
    utilprocs.log("BRO Deployment Completed ")


def deploy_graphdb(options={}, wait=True):
    utilprocs.log("Deploying GraphDB")
    helm_deploy_chart(
        CHART_NAME,
        HELM_REPO,
        BASELINE_CHART_VERSION,
        options,
        timeout=900,
        wait=wait)
    utilprocs.log(
        f'Deployment of GraphDB {"completed" if wait else "in progress"}')
