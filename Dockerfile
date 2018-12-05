FROM alpine:edge

# Add project source
WORKDIR /usr/lib/UtakoRadio
COPY . ./

# Install dependencies
RUN apk update \
&& apk add --no-cache \
  python3 \
# Install build dependencies
&& apk add --no-cache --virtual .build-deps \
  gcc \
  git \
  libffi-dev \
  make \
  musl-dev \
  python3-dev \
\
# Install pip dependencies
&& pip3 install --no-cache-dir -r dependencies.txt \
\
# Clean up build dependencies
&& apk del .build-deps

ENTRYPOINT ["python3", "main.py"]
