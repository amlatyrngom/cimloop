FROM timeloopaccelergy/timeloop-accelergy-pytorch:latest-amd64

RUN ls
RUN ls /usr/bin
RUN ls /etc/services.d/jupyter-notebook
# Overwrite the run file with my own.
RUN rm -rf /etc/services.d
COPY s6_run /etc/cont-init.d/11-run-albireo
RUN chmod +x /etc/cont-init.d/11-run-albireo


WORKDIR /home/workspace


ENTRYPOINT [ "/init" ]