# Container Security 201

Welcome to my Container Security 201 workshop!

If you haven't already, I recommend starting with my [Container Security 101 workshop](container-security-101).

Now that you have an initial familiarity with containers and standard container security controls, we're going to dig in further to see how registries and
runtimes actually work.

## Agenda

```{toctree}
---
caption: Agenda
maxdepth: 1
---
```

1. [Dig into the container image manifests, layers, and configurations](container-image-components)

## Getting started

```{important}
This lab expects that you have an AWS Cloud9 environment configured. Step by step instructions to create a Cloud9 environment are available
<a href="../ref/aws_cloud9.html" target="_blank" rel="noopener">here</a>.
```

Run the following inside your Cloud9 IDE to setup the lab environment:

<!-- This is a hidden reference config used for testing; it must be valid JSON -->
<div class="testConfig" style="display: none;">
  { "cloud9_instance_type": "t3.large" }
</div>

```{code-block} bash
---
class: getting-started
---
docker run --network host -v /:/host jonzeolla/labs:container-security-201
```

You're now ready to get started on the lab!

## Terminology

- **Image**: An image is a bundle of configuration, metadata, and files in a structured format. When you want to run a
  container, you take an image and "instantiate" (run) it.
- **Container**: A container is lightweight bundle of software that includes everything needed to run an application.
  When you run `docker run nginx`, you are taking the image `nginx` and creating a running container from it. When that
  happens, a process or set of processes are started, and a filesystem is setup. Ultimately, containers are just processes
  running on your host with a set of restrictions.
- **OCI Artifact**: In the container ecosystem, there is a standard called the _Open Container Initiative_ or OCI. It
  describes various specifications regarding [images](https://github.com/opencontainers/image-spec),
  [runtimes](https://github.com/opencontainers/runtime-spec), and [distributing
  images](https://github.com/opencontainers/distribution-spec). You don't need to worry about the details for this lab,
  just know that an OCI Artifact is a bundle of files that conforms to the OCI standards.
- **Container Runtime**: Container runtimes are software components that facilitate running containers on a host operating system. In this lab we're going to
  use `docker` as our container runtime; while there are alternatives, this is the most widely adopted containerization software and simplest place to start.

## Environment Review

After running the `jonzeolla/labs:container-security-201` docker image above, your environment was configured with some running dependencies. Let's take a look
at what was created.

<!--
1. Repo
1. Image
1. Signature?
-->

## Container image components

Alright, now it's time to get a little bit ... deeper.

So far we've covered a little bit about docker images and OCI artifacts, but what exactly _is_ an image?

You may remember from our [terminology](terminology) section that an image is a bundle of configuration, metadata, and
files in a structured format.

That bundle can be uniquely identified using an image manifest digest, which is just another name for the digest we've
been using all along. Here you can retrieve the manifest digest and use it to make API calls to the registry:

```{code-block} console
---
emphasize-lines: 3,5,7
---
$ mdigest=$(docker inspect --format='{{index .RepoDigests 0}}' example | cut -f2 -d@)
$ echo $mdigest
sha256:63e226a559065a971cfd911a91fefe7f1c96693186467ad182ca9dd9b64d078c
$ curl -k https://localhost:443/v2/example/tags/list
{"name":"example","tags":["sha256-63e226a559065a971cfd911a91fefe7f1c96693186467ad182ca9dd9b64d078c.sig","latest"]}
$ curl -s -k https://localhost:443/v2/example/manifests/$mdigest | sha256sum
63e226a559065a971cfd911a91fefe7f1c96693186467ad182ca9dd9b64d078c  -
$ curl -s -k https://localhost:443/v2/example/manifests/$mdigest | head -14
{
   "schemaVersion": 2,
   "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
   "config": {
      "mediaType": "application/vnd.docker.container.image.v1+json",
      "size": 7705,
      "digest": "sha256:6b7f86a3d64be8fb0ece35d5b54b15b6bd117c7fdcf2f778350de9012186fd14"
   },
   "layers": [
      {
         "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
         "size": 31418228,
         "digest": "sha256:26c5c85e47da3022f1bdb9a112103646c5c29517d757e95426f16e4bd9533405"
      },
```

Note that the digest is the same on each of the above highlighted lines, even the one that is the result of a
`sha256sum`, showing that it is a content addressable store. That is, the contents of the data returned by the API are
the same as its SHA-256 sum.

You can repeat this same sort of approach for the other two key components of an image; let's look at the first file
system layer first:

```{code-block} console
---
emphasize-lines: 9-18
---
$ mdigest=$(docker inspect --format='{{index .RepoDigests 0}}' example | cut -f2 -d@)
$ ldigest=$(curl -s -k https://localhost:443/v2/example/manifests/$mdigest | jq -r '.layers[0].digest')
$ echo $ldigest
sha256:26c5c85e47da3022f1bdb9a112103646c5c29517d757e95426f16e4bd9533405
$ curl -s -k https://localhost:443/v2/example/blobs/$ldigest | sha256sum
26c5c85e47da3022f1bdb9a112103646c5c29517d757e95426f16e4bd9533405  -
$ curl -s -k https://localhost:443/v2/example/blobs/$ldigest | tar -tvzf - > image_filesystem
$ head image_filesystem
lrwxrwxrwx 0/0               0 2023-11-20 00:00 bin -> usr/bin
drwxr-xr-x 0/0               0 2023-09-29 20:04 boot/
drwxr-xr-x 0/0               0 2023-11-20 00:00 dev/
drwxr-xr-x 0/0               0 2023-11-20 00:00 etc/
-rw------- 0/0               0 2023-11-20 00:00 etc/.pwd.lock
-rw-r--r-- 0/0            3040 2023-05-25 15:54 etc/adduser.conf
drwxr-xr-x 0/0               0 2023-11-20 00:00 etc/alternatives/
-rw-r--r-- 0/0             100 2023-05-11 02:04 etc/alternatives/README
lrwxrwxrwx 0/0               0 2022-06-17 15:35 etc/alternatives/awk -> /usr/bin/mawk
lrwxrwxrwx 0/0               0 2022-06-17 15:35 etc/alternatives/awk.1.gz -> /usr/share/man/man1/mawk.1.gz
```

What's particularly notable here is that we can actually start to investigate the files that are in this layer!

Now, why is it called a layer? Well, the filesystem for images is built on something called the Union filesystem, or
Unionfs. It allows us to have multiple different bundles of files (layers) which are then iteratively decompressed on
top of each other when you run a container to then create the final, merged filesystem that you actually see at runtime.

This also means that, just because a file has a certain set of contents at runtime doesn't mean that's the _only_
version of that file in the image. You may find a different file in a prior layer that was overwritten by the newer
layer.

This is where we can encounter security issues. These files become "hidden" at runtime, but they are very much available
in the image itself, if you know where to look, and sometimes they can contain sensitive information such as passwords
or keys.

Okay, let's move onto the third and final component of an image, the configuration!

```{code-block} console
---
emphasize-lines: 8-11,13-17
---
$ mdigest=$(docker inspect --format='{{index .RepoDigests 0}}' example | cut -f2 -d@)
$ cdigest=$(curl -s -k https://localhost:443/v2/example/manifests/$mdigest | jq -r '.config.digest')
$ echo $cdigest
sha256:6b7f86a3d64be8fb0ece35d5b54b15b6bd117c7fdcf2f778350de9012186fd14
$ curl -s -k https://localhost:443/v2/example/blobs/$cdigest | sha256sum
6b7f86a3d64be8fb0ece35d5b54b15b6bd117c7fdcf2f778350de9012186fd14  -
$ curl -s -k https://localhost:443/v2/example/blobs/$cdigest | jq -r '.config.Env[]'
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
NGINX_VERSION=1.23.4
NJS_VERSION=0.7.11
PKG_RELEASE=1~bullseye
$ curl -s -k https://localhost:443/v2/example/blobs/$cdigest | jq -r '.history[16]'
{
  "created": "2023-04-26T00:50:44.615696269Z",
  "created_by": "RUN /bin/sh -c groupadd --gid 53150 -r notroot && useradd -r -g notroot -s \"/bin/bash\" --create-home --uid 53150 notroot # buildkit",
  "comment": "buildkit.dockerfile.v0"
}
```

Just like with the layers, we can see some very interesting information by dissecting an image configuration. In the
highlighted lines above we see the environment variables that this image has configured, as well as some of the
historical steps taken at build time. Specifically, I am showing the user creation step from earlier in the lab.

This information is available to anybody who can pull the image, and is another place where you may find sensitive
information exposed unintentionally. For instance, was a secret passed in at build time and used to pull code from your
internal repositories? Or perhaps a secret is needed at runtime to decrypt some files and it's stored as an environment
variable. Both of those are easily exposed to anybody with read access.

The real solution here is to avoid secrets from being stored in your images in the first place. While there are many
reasonable approaches to prevent this, I highly recommend [multi-stage
builds](https://docs.docker.com/build/building/multi-stage/) and providing secrets at build time safely using
[environment variables](https://github.com/moby/buildkit/pull/1534), and dynamically retrieving sensitive information at
runtime via integrations with secrets stores like [HashiCorp Vault](https://www.vaultproject.io/), [AWS Secrets
Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html), etc.

```{note}
As a brief aside, if using `curl` to custom-create API queries isn't your thing, but you still need to take a peek under
the covers from time to time, I recommend using
[`crane`](https://github.com/google/go-containerregistry/blob/main/cmd/crane/doc/crane.md).
```

```{seealso}
Want more like the above? Well, to start I recommend checking out
[this](https://raesene.github.io/blog/2023/02/11/Fun-with-Containers-adding-tracking-to-your-images/) incredibly
interesting blog post about how OCI images can be modified to track when it's pulled, and anything online from a group
that calls themselves SIG-Honk.

Also, keep an eye out for additional labs by myself in the future 😉
```

## Conclusion

If you've made it this far, congratulations!

Have any ideas or feedback on this lab? Connect with me [on LinkedIn](https://linkedin.com/in/jonzeolla/) and send me a
message.

If you'd like more content like this, check out SANS [SEC540 class](http://sans.org/sec540) for 5 full days of Cloud
Security and DevSecOps training.

## Cleanup

Don't forget to clean up your Cloud9 environment! Deleting the environment will terminate the EC2 instance as well.