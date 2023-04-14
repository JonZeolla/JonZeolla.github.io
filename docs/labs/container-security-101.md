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

Also, in our environment we're going to use `docker` for the examples. While there are alternatives, this is the most widely adopted and simplest
place to start.

## Terminology

A quick aside on terminology.

- **Image**: An image is a bundle of configuration, metadata, and files in a structured format. When you want to run a container, you take an image
  and "instantiate" (run) it.
- **Container**: A container is lightweight bundle of software that includes everything needed to run an application. When you run `docker run nginx`,
  you are taking the image `nginx` and creating a running container from it. When that happens, a process or set of processes are started, and a
  filesystem is setup. Ultimately, containers are just processes running on your host with a set of restrictions.
- **OCI Artifact**: In the container ecosystem, there is a standard called the _Open Container Initiative_ or OCI. It describes various
  specifications regarding [images](https://github.com/opencontainers/image-spec), [runtimes](https://github.com/opencontainers/runtime-spec), and
  [distributing images](https://github.com/opencontainers/distribution-spec). You don't need to worry about the details for this lab, just know that
  an OCI Artifact is a bundle of files that conforms to the OCI standards.

For more background, see docker's [What is a Container?](https://www.docker.com/resources/what-container/) page.

## Creating images

As described in [the terminology section](#terminology), images are bundles. Those bundles need to be created (or "built"), and the primary way that
we do that is by creating a `Dockerfile`. For instance:

```{code-block} bash
---
class: no-copybutton
---
FROM nginx
WORKDIR /
RUN ls -al
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
EXPOSE 80
```

In the above example, you see that we are starting with `FROM nginx`. This means two things:
1. We are implicitly using the special `latest` tag of `nginx` (see other available tags [here](https://hub.docker.com/_/nginx/tags)).
1. We are also implicitly pulling the images from Docker Hub, which is the default [Registry](https://docs.docker.com/registry/) for `docker`.

Based on these two items, `FROM nginx` is functionally equivalent to `FROM docker.io/nginx:latest`.

### Unsafe default configurations

There are a myriad of ways a container or image can be insecure. My favourite way to quickly scan a `Dockerfile` to find issues is to use
[hadolint](https://github.com/hadolint/hadolint)'s out-of-the-box rules, and if you need more customized options I would look at
[conftest](https://www.conftest.dev/) from the Open Policy Agent (OPA) project (you can check out an example `Dockerfile` policy
[here](https://github.com/open-policy-agent/conftest/tree/master/examples/docker)).

In our example, the image we were just looking at above does not define a `USER`:

```{code-block} console
$ docker inspect nginx:latest | jq '.[].Config.User'
""
```

This configuration is unsafe, because when the user is empty or unspecified, it will default to using the `root` user.

Another way to check for the user in use is by running `whoami` while the container is running.

```{code-block} console
$ docker run nginx:latest whoami
root
```

### Changing the user

Running as `root` is not preferred, and although there are [ways to secure](https://docs.docker.com/engine/security/userns-remap/) a process that must
run as `root`, it should not be the default. So, let's fix that.

We'll start by making a temporary working area:

```{code-block} console
$ newdir=$(mktemp -d)
$ pushd "${newdir}"
```

And then we create a more secure `Dockerfile`:

```{code-block} bash
cat << EOF > Dockerfile
FROM nginx
WORKDIR /
RUN ls -al
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
EXPOSE 80
RUN groupadd --gid 53150 -r notroot \
 && useradd -r -g notroot -s "$(which bash)" --create-home --uid 53150 notroot
 USER notroot
EOF
```

Now we can build the more secure image! Note the user on the last line is _not_ the root user. Success!

```{code-block} console
---
emphasize-lines: 4
---
$ docker build -t example-secure .
$ popd
$ docker inspect example-secure | jq -r '.[].Config.User'
notroot
```

You can also confirm that the container will not use the root user by default by running the container and checking the current user.

```{code-block} console
$ docker run example-secure whoami
notroot
```

Does this mean it's impossible to run this container insecurely? Absolutely not! For instance, let's re-run that command with one additional argument,
asking it to use the `root` user explicitly.

```{code-block} console
$ docker run --user 0 example-secure whoami
root
```

All we've done is make a more secure configuration _the default_, not impossible. In order to further secure your container runtimes requires a host
of additional layers of security; what we generally refer to as Policy as Code. Check back in the future for a lab on that 😀

## Image signing

### What is it?

### Why?

### How?

```{code-block} bash
---
class: no-copybutton
---
TODO
```

## Vulnerability scanning images

### Approaches

SBOM generate-then-scan

Scan the image

Scan the repository

Why is scan the image better than repository?

```{note}
---
class: dropdown
---
Changes to the code can happen during build, including bringing in new dependences, or different versions of known dependencies.

While containers could technicall also make those changes at runtime, it is significantly less popular and easier to monitor for/prevent.
```

## Container image components

High level explanation

### Manifests

```{code-block} console
$ docker run cgr.dev/chainguard/crane
output example here
```

What part of this output is most interesting?

:::{admonition} Answer
---
class: dropdown hint
---
```{code-block} bash
---
class: no-copybutton
emphasize-lines: 2
---
$ docker run cgr.dev/chainguard/crane
output example here
```
:::

### Index

### Layers

```{seealso}
---
name: oci-image-teardown
---
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
