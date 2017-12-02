FROM python:3.6

RUN apt-get update \
	&& apt-get install -yq --fix-missing ca-certificates nginx gettext-base supervisor

RUN pip install uwsgi

## #################
##      ffmpeg
## #################

# Installation Instructions:
## https://trac.ffmpeg.org/wiki/CompilationGuide/Ubuntu
### Changes from the mentioned instructions are marked with: (!)

# Get the dependencies
RUN apt-get update -qq && apt-get -y install \
  autoconf \
  automake \
  build-essential \
  cmake \
  git \
  libass-dev \
  libfreetype6-dev \
  libsdl2-dev \
  libtheora-dev \
  libtool \
  libva-dev \
  libvdpau-dev \
  libvorbis-dev \
  libxcb1-dev \
  libxcb-shm0-dev \
  libxcb-xfixes0-dev \
  mercurial \
  pkg-config \
  texinfo \
  wget \
  zlib1g-dev

# Make a new directory in home, to put all of the source code and binaries into
RUN mkdir -p ~/ffmpeg_sources ~/bin

# NASM
RUN cd ~/ffmpeg_sources && \
wget http://www.nasm.us/pub/nasm/releasebuilds/2.13.01/nasm-2.13.01.tar.bz2 && \
tar xjvf nasm-2.13.01.tar.bz2 && \
cd nasm-2.13.01 && \
./autogen.sh && \
PATH="$HOME/bin:$PATH" ./configure --prefix="$HOME/ffmpeg_build" --bindir="$HOME/bin" && \
make && \
make install

# Yasm
RUN apt-get -y install yasm

# libx264
RUN apt-get -y install libx264-dev

# cmake (!)
## usage: /opt/cmake/bin/cmake
RUN wget https://cmake.org/files/v3.10/cmake-3.10.0.tar.gz && \
tar xzf cmake-3.10.0.tar.gz && \
cd cmake-3.10.0 && \
./configure --prefix=/opt/cmake && \
make && \
make install

# libx265 (!)
RUN cd ~/ffmpeg_sources && \
if cd x265 2> /dev/null; then hg pull && hg update; else hg clone https://bitbucket.org/multicoreware/x265; fi && \
cd ~/ffmpeg_sources/x265/build/linux && \
PATH="$HOME/bin:$PATH" /opt/cmake/bin/cmake -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX="$HOME/ffmpeg_build" -DENABLE_SHARED:bool=off ../../source && \
PATH="$HOME/bin:$PATH" make && \
make install

# libvpx
RUN cd ~/ffmpeg_sources && \
git -C libvpx pull 2> /dev/null || git clone --depth 1 https://chromium.googlesource.com/webm/libvpx.git && \
cd libvpx && \
PATH="$HOME/bin:$PATH" ./configure --prefix="$HOME/ffmpeg_build" --disable-examples --disable-unit-tests --enable-vp9-highbitdepth --as=yasm && \
PATH="$HOME/bin:$PATH" make && \
make install

# libfdk-aac
RUN cd ~/ffmpeg_sources && \
git -C fdk-aac pull 2> /dev/null || git clone --depth 1 https://github.com/mstorsjo/fdk-aac && \
cd fdk-aac && \
autoreconf -fiv && \
./configure --prefix="$HOME/ffmpeg_build" --disable-shared && \
make && \
make install

# libmp3lame
RUN apt-get -y install libmp3lame-dev

# libopus
RUN apt-get -y install libopus-dev

# libass (!)
RUN apt-get -y install libass-dev

# libtheora (!)
RUN apt-get -y install libtheora-dev

# libvorbis (!)
RUN apt-get -y install libvorbis-dev

# FFmpeg
## usage: ~/bin/ffmpeg
RUN cd ~/ffmpeg_sources && \
wget -O ffmpeg-snapshot.tar.bz2 http://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2 && \
tar xjvf ffmpeg-snapshot.tar.bz2 && \
cd ffmpeg && \
PATH="$HOME/bin:$PATH" PKG_CONFIG_PATH="$HOME/ffmpeg_build/lib/pkgconfig" ./configure \
  --prefix="$HOME/ffmpeg_build" \
  --pkg-config-flags="--static" \
  --extra-cflags="-I$HOME/ffmpeg_build/include" \
  --extra-ldflags="-L$HOME/ffmpeg_build/lib" \
  --extra-libs="-lpthread -lm" \
  --bindir="$HOME/bin" \
  --enable-gpl \
  --enable-libass \
  --enable-libfdk-aac \
  --enable-libfreetype \
  --enable-libmp3lame \
  --enable-libopus \
  --enable-libtheora \
  --enable-libvorbis \
  --enable-libvpx \
  --enable-libx264 \
  --enable-libx265 \
  --enable-nonfree && \
PATH="$HOME/bin:$PATH" make && \
make install

# symlink to ffmpeg binary
RUN cd /usr/bin && \
ln -s ~/bin/ffmpeg ffmpeg && \
source ~/.profile


## #################
##      Nginx
## #################

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log \
	&& echo "daemon off;" >> /etc/nginx/nginx.conf \
	&& rm /etc/nginx/sites-enabled/default

# Copy the modified Nginx conf
COPY ./docker/nginx.conf /etc/nginx/conf.d/
# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY ./docker/uwsgi.ini /etc/uwsgi/


## #################
##   Supervisord
## #################

# Custom Supervisord config
COPY ./docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf


## #################
##     Project
## #################
COPY  ./project/ /project/
WORKDIR /project

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80 443
CMD ["/usr/bin/supervisord"]
