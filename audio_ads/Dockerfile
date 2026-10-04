ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache \
    bash \
    ca-certificates \
    ffmpeg \
    python3 \
    py3-pip \
    py3-numpy \
    tzdata \
    && pip3 install --no-cache-dir --break-system-packages \
       flask==3.1.0 edge-tts==7.2.3 mutagen==1.47.0

WORKDIR /app
COPY app /app
COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8099
CMD ["/run.sh"]
