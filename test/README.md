# Testing strategy for GraphDB

## How to run the tests

### Prerequisites

* Have Python 3 installed
* Have Pip 3 installed

### Install git submodules

Before running the tests, make sure you have the
testframework submodule initialised.
This can be done as follows:

````bash
git submodule sync
git submodule update --init --recursive
````

### Install python dependencies

Next, you must install the Python dependencies for the testframework.
From the root of the project, run the following:

````bash
pip3 install -r ./testframework/requirements.txt
````

### Verify python dependencies

After installing the dependencies, you may wish to verify that
you have the correct versions of the dependencies installed.
You can verify that you have the correct versions of the
dependencies installed by running the following command:

````bash
while read -r line; do IFS='=';
read -r -a array <<< ${line};
installed="`pip3 freeze | grep ${array[0]}`";
echo "Required $line installed $installed";
done < testframework/requirements.txt
````

For each of the dependencies, this command will
print out the version of the dependency required
and the version which your system has installed.
It will be in the following format:

`Required kubernetes==6.0.0 installed kubernetes==6.0.0`

From this, you will be able to see if there are
any discrepencies between what is required and
what is installed on your system.
In most cases, it will not be an issue if
there are differences in the MINOR or PATCH number.
However, if there are differences in the MAJOR number,
you should resolve the difference be installing the correct version.

### Tests

GraphDB has following stages for running the test

1- Test Deploy
This test deploys the GraphDB in K8s environment and runs tests for GraphDB

2- BUR-Test

This test deploys GraphDB and BRO on K8s environment
and afterwards it runs the test for Backup and Restore of GraphDB.

### Running the tests

Tests are run by executing the following on the command line.
It should be run from the root directory of the GraphDB project.

Environment variables needed to run tests are:

````text
1-Path to K8s conf to use for test environment:
    export KUBECONFIG=$HOME/.kube/config

2-Path to Neo4j helm chart to test:
    export chart_archive="/tmp/eric-data-graph-database-nj-0.0.1-hc437c8c.tgz"

3- URL of Helm chart repository for GraphDB:
    export helm-repo=https://arm.seli.gic.ericsson.se/artifactory/list/proj-adp-oss-graph-database-nj-helm/

4- GraphDB chart version:
    export baseline_chart_version="0.0.1-hc437c8c"

5- GraphDB chart name to deploy:
    export baseline_chart_name="eric-data-graph-database-nj"

6- Any values for test-params can be set to use in test:
   e.g.
   --test-params bro-version=2.3.0-8
   sets the variable bro-version to a value 2.3.0-8
   later to be used.
````

To run tests in Test Deploy stage

````bash
python3 -u testframework/bootstrap.py
--kubernetes-admin-conf=$KUBECONFIG
--chart-archive=$chart-archive
--helm-repo=$helm-chart-repo
--baseline_chart_version=$baseline_chart_version
--baseline_deployment_type="deployment"
--baseline_chart_name=$helm-chart-name
--test-params unused1=1
--fail-first=True
-s test_graphdb.py
````

Test Deploy example on local machine.

```bash
python3 -u testframework/bootstrap.py
--kubernetes-admin-conf=$KUBECONFIG
--chart-archive="/tmp/eric-data-graph-database-nj-0.0.1-hc437c8c.tgz"
--helm-repo="https://arm.seli.gic.ericsson.se/artifactory/list/proj-adp-oss-graph-database-nj-helm/"
--baseline_chart_version="0.0.1-hc437c8c"
--baseline_deployment_type="deployment"
--baseline_chart_name="eric-data-graph-database-nj"
--test-params unused1=1
--fail-first=True
-s test_graphdb.py
````

For running tests in BUR-Test stage

````bash
python3 -u testframework/bootstrap.py
--kubernetes-admin-conf=$KUBECONFIG
--chart-archive=$chart-archive
--helm-repo=$helm-chart-repo
--baseline_chart_version=$baseline_chart_version
--baseline_deployment_type="deployment"
--baseline_chart_name=$helm-chart-name
--test-params bro-version=$bro-version
bro-helm-repo=$bro-helm-repo
bro-chart-name=$bro-chart-name
--fail-first=True
-s test_bur.py
````

BUR test example on local machine.

```bash
python3 -u testframework/bootstrap.py
--chart-archive="/tmp/eric-data-graph-database-nj-0.0.1-hc437c8c.tgz"
--helm-repo="https://arm.seli.gic.ericsson.se/artifactory/list/proj-adp-oss-graph-database-nj-helm/"
--baseline_chart_version="0.0.1-hc437c8c"
--baseline_deployment_type="deployment"
--baseline_chart_name="eric-data-graph-database-nj"
-p bro-version=2.3.0-8
bro-helm-repo=https://arm.rnd.ki.sw.ericsson.se/artifactory/proj-adp-gs-all-helm/
bro-chart-name=eric-ctrl-bro
--kubernetes-admin-conf=$KUBECONFIG
--fail-first=True
-s test_bur.py
````

Note: **Don't forget the  -u flag.**
Logs will be written out of order if you forget it.
When the tests are being run by Bob
(as part of our Jenkins pipeline), Bob uses
environment variables to configure the tests.
These environment variables are set in `ruleset.yaml`.

## Summary of Testing Strategy
