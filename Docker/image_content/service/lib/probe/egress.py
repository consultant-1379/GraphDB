from pyu.ui.egress import ExitCodesBase


class ExitCode(ExitCodesBase):
    successful = 0
    healthcheck_disabled = 0
    not_running = 1
    not_listening = 2
    not_pinging = 3
    no_consistent_routing = 4
    cpu_exhausted = 5
    internal_error = 0
    # internal_error AS ZERO BECAUSE IT'S TOO RISKY TO ALLOW K8S TO RESTART
    # THE CONTAINER FOR ANY UNKNOWN FAILURE
