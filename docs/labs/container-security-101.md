# Container Security 101

Welcome to my Container Security 101 workshop! If you'd like to sign up, you can register
[here](https://www.sans.org/webcasts/container-security-101/).

## Agenda

1. Create secure and insecure container images.
1. Perform container image signing.
1. Create SBOMs.
1. Vulnerability scan the images.
1. Dig into the container image manifests, indexes, and layers.
1. Break out of a misconfigured container.

## Getting started

```{important}
This lab expects that you are running on Ubuntu 20.04 x86; see [this guide](../ref/aws_ubuntu20.04.md) if you need help setting that up.
```

This lab is meant to be run in order from top to bottom. If you skip around, it is possible some prerequisites may not be met and you will encounter
errors.

## Create images

### Insecure

### Secure

## Image signing

### What is it?

### Why?

### How?

```console

```

## Vulnerability scanning images

### Approaches

SBOM generate-then-scan

Scan the image

Scan the repository

Why is scan the image better than repository?

```{tip}
:class: dropdown

Changes to the code can happen during build, including bringing in new dependences, or different versions of known dependencies.

While containers could technicall also make those changes at runtime, it is significantly less popular and easier to monitor for/prevent.
```

## Container image components

High level explanation

### Manifests

```console
$ docker run cgr.dev/chainguard/crane
output example here
```

### Index

### Layers

```{seealso}
:name: oci-image-teardown
If you want more hands-on teardown of OCI images, see my OCI image teardown lab [here](./oci-image-teardown.md)
```

## Read, Set, Break!

### Successful breakout

### Fix

### Failed breakout


## Container Breakout

TODO

## More

Looking for more content like this? Take a look at the SANS [SEC540 class](http://sans.org/sec540)!
