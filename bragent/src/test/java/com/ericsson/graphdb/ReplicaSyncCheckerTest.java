package com.ericsson.graphdb;

import static org.junit.Assert.assertEquals;
import static org.mockito.Mockito.*;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.neo4j.driver.exceptions.ClientException;
import org.powermock.api.mockito.PowerMockito;
import org.powermock.core.classloader.annotations.PrepareForTest;
import org.powermock.modules.junit4.PowerMockRunner;


@RunWith(PowerMockRunner.class)
@PrepareForTest({ReplicaSyncChecker.class})
public class ReplicaSyncCheckerTest {

    ReplicaSyncChecker rs;

    @Before
    public void setUp() throws Exception {
        PowerMockito.mockStatic(System.class);
        PowerMockito.when(System.getenv("NEO4J_causal__clustering_initial__discovery__members")).thenReturn("core_host:23,host_2:23,host_3:23");
        PowerMockito.when(System.getenv("NEO4J_PORT_BOLT")).thenReturn("124");
        PowerMockito.when(System.getenv("PRE_BACKUP_REPLICA_SYNC_TIMEOUT")).thenReturn("300s");
        PowerMockito.mockStatic(Thread.class);
        rs = PowerMockito.spy(new ReplicaSyncChecker());
        PowerMockito.doReturn("password", "12345").when(rs, "getNeo4jAdminPassword");
    }

    @Test
    public void replicaSyncCheckSuccess() throws Exception  {
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        assertEquals(rs.isReplicaSyncSuccessful(), true);
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeFound");
    }

    @Test
    public void replicaSyncLeaderDriverSetAfterTwoTries() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L);
        PowerMockito.doReturn(false, true).when(rs, "isLeaderDriverSet");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        assertEquals(rs.isReplicaSyncSuccessful(), true);
        PowerMockito.verifyPrivate(rs, times(2)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeFound");
    }

    @Test
    public void replicaSyncBurFlagFoundAfterTwoTries() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L);
        PowerMockito.doReturn(false, true).when(rs, "isBurFlagNodeFound");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        assertEquals(rs.isReplicaSyncSuccessful(), true);
        PowerMockito.verifyPrivate(rs, times(2)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(2)).invoke("isBurFlagNodeFound");
    }

    @Test
    public void replicaSyncCreateNodeSuccessfulAfterTwoTries() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L);
        PowerMockito.doReturn(false, true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        assertEquals(rs.isReplicaSyncSuccessful(), true);
        PowerMockito.verifyPrivate(rs, times(2)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(2)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeFound");
    }

    @Test
    public void replicaSyncLeaderDriverSetFailUntilTimeout() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L).thenReturn(0L).thenReturn(999999999L);
        PowerMockito.doReturn(false).when(rs, "isLeaderDriverSet");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        assertEquals(rs.isReplicaSyncSuccessful(), false);
    }

    @Test
    public void replicaSyncBurFlagNotFoundUntilTimeout() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L).thenReturn(0L).thenReturn(999999999L);
        PowerMockito.doReturn(false).when(rs, "isBurFlagNodeFound");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        assertEquals(rs.isReplicaSyncSuccessful(), false);
    }

    @Test
    public void replicaSyncCreateNodeFailUntilTimeout() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L).thenReturn(0L).thenReturn(999999999L);
        PowerMockito.doReturn(false).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        assertEquals(rs.isReplicaSyncSuccessful(), false);
    }

    @Test
    public void replicaNeo4jExceptionThrownThriceUntilTimeout1() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L).thenReturn(0L).thenReturn(0L).thenReturn(0L).thenReturn(999999999L);
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        PowerMockito.doThrow(new ClientException("Error")).when(rs, "removeBurFlagNodes");
        assertEquals(rs.isReplicaSyncSuccessful(), false);
        PowerMockito.verifyPrivate(rs, times(3)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(3)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(0)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(0)).invoke("isBurFlagNodeFound");
    }

    @Test
    public void replicaNeo4jExceptionThrownThriceUntilTimeout2() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L).thenReturn(0L).thenReturn(0L).thenReturn(0L).thenReturn(999999999L);
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeFound");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doThrow(new ClientException("Error")).when(rs, "isBurFlagNodeCreateSuccessful");
        assertEquals(rs.isReplicaSyncSuccessful(), false);
        PowerMockito.verifyPrivate(rs, times(3)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(3)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(0)).invoke("isBurFlagNodeFound");
    }

    @Test
    public void replicaNeo4jExceptionThrownThriceUntilTimeout3() throws Exception  {
        PowerMockito.when(System.currentTimeMillis()).thenReturn(0L).thenReturn(0L).thenReturn(0L).thenReturn(0L).thenReturn(999999999L);
        PowerMockito.doReturn(true).when(rs, "isLeaderDriverSet");
        PowerMockito.doReturn(true).when(rs, "isBurFlagNodeCreateSuccessful");
        PowerMockito.doNothing().when(rs, "removeBurFlagNodes");
        PowerMockito.doThrow(new ClientException("Error")).when(rs, "isBurFlagNodeFound");
        assertEquals(rs.isReplicaSyncSuccessful(), false);
        PowerMockito.verifyPrivate(rs, times(3)).invoke("isLeaderDriverSet");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("removeBurFlagNodes");
        PowerMockito.verifyPrivate(rs, times(1)).invoke("isBurFlagNodeCreateSuccessful");
        PowerMockito.verifyPrivate(rs, times(3)).invoke("isBurFlagNodeFound");
    }

}
