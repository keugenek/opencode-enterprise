# Build from enterprise/ as context after copying in the patched CLI binary.
# Supply a vetted Linux runtime image by immutable digest. Must contain CA roots,
# git, rg, bash, and the toolchain required by the target project; no Docker socket.
ARG RUNTIME_IMAGE
FROM ${RUNTIME_IMAGE}
USER root
RUN mkdir -p /etc/opencode /workspace /home/opencode /tmp \
    && chown 10001:10001 /workspace /home/opencode \
    && chmod 0755 /etc/opencode
COPY --chown=0:0 --chmod=0644 enterprise.example.json /etc/opencode/enterprise.json
COPY --chown=0:0 --chmod=0755 opencode /usr/local/bin/opencode
ENV HOME=/home/opencode \
    XDG_CONFIG_HOME=/home/opencode/.config \
    XDG_DATA_HOME=/home/opencode/.local/share \
    XDG_CACHE_HOME=/home/opencode/.cache \
    OPENCODE_DISABLE_SHARE=true \
    OPENCODE_DISABLE_AUTOUPDATE=true \
    OPENCODE_DISABLE_MODELS_FETCH=true \
    OPENCODE_PURE=true \
    OTEL_SDK_DISABLED=true \
    DO_NOT_TRACK=1
USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/opencode"]
