/*------------------------------------------------------------------------------
 *******************************************************************************
 * COPYRIGHT Ericsson 2021
 *
 * The copyright to the computer program(s) herein is the property of
 * Ericsson Inc. The programs may be used and/or copied only with written
 * permission from Ericsson Inc. or in accordance with the terms and
 * conditions stipulated in the agreement/contract under which the
 * program(s) have been supplied.
 *******************************************************************************
 *----------------------------------------------------------------------------*/

package com.ericsson.graphdb;

import java.io.*;
import java.util.logging.Logger;

import org.neo4j.driver.AccessMode;
import org.neo4j.driver.AuthTokens;
import org.neo4j.driver.Bookmark;
import org.neo4j.driver.Driver;
import org.neo4j.driver.GraphDatabase;
import org.neo4j.driver.Result;
import org.neo4j.driver.Session;
import org.neo4j.driver.SessionConfig;
import org.neo4j.driver.exceptions.Neo4jException;
import org.neo4j.driver.exceptions.TransientException;

public class ReplicaSyncChecker {

    private static final Logger log = Logger.getLogger(ReplicaSyncChecker.class.getName());

    private static final String ADDRESSES = System.getenv("NEO4J_causal__clustering_initial__discovery__members");

    private static final String USER = "neo4j";

    private static final String BOLT_PORT = System.getenv("NEO4J_PORT_BOLT");

    private static final String TIMEOUT_SECS = System.getenv("PRE_BACKUP_REPLICA_SYNC_TIMEOUT");

    private static final String REPLICA_URL = String.format("bolt://localhost:%s", BOLT_PORT);

    private String cachedPassword = null;

    private Driver replicaDriver = null;

    private Driver coreDriver = null;

    private Long nodeId = null;

    private Bookmark bmark = null;

    private boolean isRemoveNodeExecuted = false;

    private boolean isCreateNodeExecuted = false;

    private String executeCommand(String[] command) throws IOException, InterruptedException {
        StringBuffer output = new StringBuffer();
        StringBuffer error = new StringBuffer();
        Process p = Runtime.getRuntime().exec(command);
        p.waitFor();
        BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
        BufferedReader stdError = new BufferedReader(new InputStreamReader(p.getErrorStream()));
        String line = "";
        while ((line = reader.readLine()) != null) {
            output.append(line + "\n");
        }
        while ((line = stdError.readLine()) != null) {
            error.append(line + "\n");
        }
        if (error.length() > 0) {
            throw new IOException("Failed to run command");
        }
        return output.toString();
    }

    private String getNeo4jAdminPassword() throws IOException, InterruptedException {
        if ( this.cachedPassword == null ) {
            String[] cmd = {"python3", "-c",
                            "from neo4jlib.client.base import LocalNeo4jClient; from neo4jlib.client.auth.credentials import credentials; from pyu.decor.misc import retry_if_fail; print(retry_if_fail(10, 30)(lambda: credentials(LocalNeo4jClient()).admin.password)())"};
            this.cachedPassword = executeCommand(cmd).trim();
        }
        return this.cachedPassword;
    }

    private boolean isBurFlagNodeCreateSuccessful() throws InterruptedException {
        try (Session session = this.coreDriver.session()) {
            log.info("Creating BurFlag node");
            this.nodeId = session.writeTransaction(tx -> {
                Result result = tx.run("CREATE (a:BurFlag) RETURN id(a)");
                return result.single().get(0).asLong();
            });
            this.bmark = session.lastBookmark();
        }
        if (this.nodeId == null || this.bmark == null) {
            return false;
        }else {
            String msgNodeCreated = String.format("Node created. Core bookmark: %s; Node id: %d.  %n Now pausing for 10 seconds for the node to be synchronized", this.bmark, this.nodeId);
            log.info(msgNodeCreated);
            Thread.sleep(10000L);
            return true;
        }
    }

    private boolean isBurFlagNodeFound() throws IOException, InterruptedException {
        try {
            log.info("ReplicaSyncChecker::isBurFlagNodeFound(): Before acquiring the Driver");
            this.replicaDriver = GraphDatabase.driver(REPLICA_URL, AuthTokens.basic(USER, getNeo4jAdminPassword()));
            log.info("ReplicaSyncChecker::isBurFlagNodeFound(): Before acquiring session withBookMark");
            try (Session session = this.replicaDriver.session(SessionConfig.builder().withBookmarks(this.bmark).build())) {
                String msgBurNode = String.format("Getting BurFlag node from replica with id: %s",  this.nodeId);
                log.info(msgBurNode);
                Long rNode = session.readTransaction(tx -> {
                     Result result = tx.run("MATCH (a:BurFlag) WHERE id(a) = " + this.nodeId + " RETURN id(a)");
                 return result.single().get(0).asLong();
                });
                if (rNode.equals(this.nodeId)) {
                    String msgReplicaFound = String.format("Replica found newly created node; Id: %d", rNode);
                    log.info(msgReplicaFound);
                    return true;
                }else {
                    return false;
                }
            }catch(TransientException e) {
                //TransientException: Database not up to the requested version: 106451. Latest database version is 106449.
                //It could be a trasient, retry in few seconds.
                log.warning("Caught Transient Exception:"+e.getMessage());
                Thread.sleep(4000L);
            }catch(Neo4jException ne) {
                log.warning("Caught Neo4j Exception:"+ne.getMessage());
            }catch(Exception ex) {
                log.warning("Caught Exception:"+ex.getMessage());
            }
        } finally {
            if (this.replicaDriver != null) {
                this.replicaDriver.close();
            }
        }
        return false;
    }

    private void removeBurFlagNodes() {
        try (Session session = this.coreDriver.session()) {
            log.info("Removing any BurFlag nodes");
            session.writeTransaction(tx -> {
                tx.run("MATCH (a:BurFlag) DETACH DELETE a;");
                return "";
            });
            log.info("BurFlag nodes removed.");
        }
    }

    private boolean isLeaderDriverSet() throws IOException, InterruptedException {
        String[] addressList = ADDRESSES.split(",");
        for (String address : addressList) {
            String addressHost = address.split(":")[0];
            System.out.println(addressHost);
            String host_uri = String.format("neo4j://%s:%s", addressHost, BOLT_PORT);
            this.coreDriver = GraphDatabase.driver(host_uri, AuthTokens.basic(USER, getNeo4jAdminPassword()));
            try {
                try (Session session = this.coreDriver.session(SessionConfig.builder().withDefaultAccessMode(AccessMode.WRITE).build())) {
                    Result result = session.run("CALL db.ping()");
                    if (result.single().get("success").asBoolean()) {
                        log.info("Leader driver has been successfully set");
                        return true;
                    }
                }
            } catch (Neo4jException e) {
                log.warning(e.toString());
            }
        }
        return false;
    }

    public boolean isReplicaSyncSuccessful() throws IOException, InterruptedException {
        int timeoutSecs = Integer.parseInt(TIMEOUT_SECS.split("s")[0]);
        int timeoutMillis = timeoutSecs * 1000;
        long endTime = System.currentTimeMillis() + timeoutMillis;
        while (System.currentTimeMillis() < endTime) {
            if (!isLeaderDriverSet()) {
                continue;
            }
            try {

                if (!this.isRemoveNodeExecuted) {
                    removeBurFlagNodes();
                    this.isRemoveNodeExecuted = true;
                }
                if (!this.isCreateNodeExecuted) {
                    if (isBurFlagNodeCreateSuccessful()) {
                        this.isCreateNodeExecuted = true;
                    } else {
                        continue;
                    }
                }
                if (isBurFlagNodeFound()) {
                    log.info("Read replica has been synced with the Leader and backup can proceed");
                    return true;
                }
            } catch (Neo4jException e) {
                log.info(String.format("Error communicating with Neo4j Server to check if read replica is in sync with core server: %s", e.getMessage()));
                log.info("Sleeping for one second before retrying to sync read replica with leader");
                Thread.sleep(1000L);
            } finally {
                if (coreDriver != null) {
                    coreDriver.close();
                }
            }
        }
        return false;
    }

    public static void main(String... args) {
        try {
            ReplicaSyncChecker syncChecker = new ReplicaSyncChecker();
            if (!syncChecker.isReplicaSyncSuccessful()) {
                log.severe(String.format("Synchronization of Read replica with Leader has timed out. The Read replica might not be synchronized with the leader."));
                System.exit(1);
            }
        } catch (Exception e) {
            log.severe(String.format("Error occurred, Read replica may not be in synchronized with Leader: %s", e.getMessage()));
            System.exit(1);
        }
        System.exit(0);
    }
}
