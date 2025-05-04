docker build -t mytimeloop --progress=plain .

docker run -it --rm -v $(pwd)/workspace:/home/workspace mytimeloop

docker run -it --rm -p 8888:8888 \
   -v $(pwd)/workspace:/home/workspace \
   -e USER_UID=1000 \
   -e USER_GID=1000 \
   mytimeloop
