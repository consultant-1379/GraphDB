# Contributing to the Graph Database NJ

## Gerrit Project Details

All relevant source code is accessible in the below repositories:

* [GraphDB service Git](https://gerrit.ericsson.se/#/admin/projects/AIA/microservices/GraphDB)
* [GraphDB integration charts and tests](https://gerrit.ericsson.se/#/admin/projects/AIA/microservices/GraphDB-testware)
* [GraphDB agent helm chart, ENM-specific init values and Neo4J server extensions for DPS Docker](https://gerrit.ericsson.se/gitweb?p=AIA/GraphDB-ENM.git;a=tree;h=refs/heads/master;hb=refs/heads/master)

## Documentation

All relevant documentation may be found in this repo's `Documentation/` directory.

* Graph Database NJ Service Overview
  * *Format:* asciidoc
  * *Git Path:* `Documentation/GraphDB_NJ_ServiceOverview.adoc`
* Graph Database NJ Deployment Guide
  * *Format:* asciidoc
  * *Git Path:* `Documentation/GraphDB_NJ_DeploymentGuide.adoc`
* Graph Database NJ Troubleshooting Document
  * *Format:* asciidoc
  * *Git Path:* `Documentation/GraphDB_NJ_Troubleshooting.adoc`
  
## Ownership and Service Guardians / Maintainers

This service is currently owned and maintained by Team Enigma. Please
get in touch with [Enigma](PDLENIGMAE@pdl.internal.ericsson.com) if you
wish to make changes.

## Contribution Workflow

1. The **contributor** updates the artifact in the local repository.
2. The **contributor** pushes the update to Gerrit for review.
3. The **contributor** invites the **Service Guardians** (mandatory)
 and **other relevant parties** (optional) to the Gerrit review,
and makes no further changes to the document until it is reviewed.
4. The **service guardian** reviews the document and gives a code-review score.
The code-review scores and corresponding workflow activities are as follows:

    * Score is +1
        * A **reviewer** is happy with the changes but approval is required
        from another reviewer.
    * Score is +2
        * The **service guardian** accepts the change
        * The **service guardian** ensures publication to Calstore
        * The **service guardian** ensures publication to the ADP marketplace
    * Score is -1 or -2
        * The **service guardian** and the **contributor** align to
        determine when and how the change is published.
