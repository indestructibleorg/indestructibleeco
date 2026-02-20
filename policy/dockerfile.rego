package indestructibleeco.dockerfile

deny[msg] {
    input.Cmd == "user"
    input.Value[0] == "root"
    msg := "Container must not run as root user"
}

deny[msg] {
    input.Cmd == "from"
    contains(input.Value[0], ":latest")
    msg := "Must not use :latest tag"
}

warn[msg] {
    not input.Healthcheck
    msg := "Dockerfile should include HEALTHCHECK instruction"
}
