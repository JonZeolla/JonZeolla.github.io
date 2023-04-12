# OCI Image Teardown

Welcome to my OCI Image Teardown lab!

## Agenda

1. Pull a multi-platform docker image
1. Export the docker image as an OCI artifact
1. Investigate the manifests and indexes
1. Extract "hidden" files from the layers
1.

## Getting started

```{note}
:class: dropdown

This lab expects that you are running on Ubuntu 20.04 x86; see [this guide](../ref/aws_ubuntu20.04.md) if you need help setting that up.
```

For simplicity, we will be using containers to do the OCI image teardown; it's only right!

Make sure that the `docker` daemon is installed and running.

If the following

## Pull a multi-platform OCI image

```{tip}
:class: dropdown

If you get an error starting with "docker: Cannot connect to the Docker daemon", you may need to start the daemon. Try `sudo systemctl start docker`
and then rerun the command
```


## Export the docker image as an OCI artifact

## Investigate the manifests and indexes

## Extract "hidden" files from the layers

##
