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
This lab expects that you are running on Ubuntu 20.04 x86; see [this guide](../ref/aws_ubuntu20.04.md) if you need help
setting that up.

I highly recommend using a fresh, ephemeral system, as there is no deterministic way to "undo" all of the steps below
after the workshop.
```

This lab is meant to be run in order from top to bottom. If you skip around, it is possible some prerequisites may not
be met and you will encounter errors.

Also, in our environment we're going to use `docker` for the examples. While there are alternatives, this is the most
widely adopted and simplest place to start.

Run the following to setup the prerequisite tools:

```{code-block} console
$ sudo apt-get update
$ sudo apt-get -y remove docker.io containerd runc
$ sudo apt-get -y install --no-install-recommends ca-certificates curl gnupg
$ sudo install -m 0755 -d /etc/apt/keyrings
$ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
$ sudo chmod a+r /etc/apt/keyrings/docker.gpg
$ echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
$ sudo apt-get update
$ sudo apt-get -y install --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin jq
```

```{note}
When you encounter code blocks, like above, it will show a copy button when you mouse over it if it is meant to be
copied/pasted directly.

After copy/pasting into your system, you will need to hit enter for all of the lines to be run.
```

Now, if you attempt to run `docker` commands, you will find that they fail:

```{code-block} console
$ docker ps
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get "http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/json": dial unix /var/run/docker.sock: connect: permission denied
```

In order to fix that, add your user to the `docker` group (in this example, we're updating the default `ubuntu` user).

```{code-block} console
sudo usermod -aG docker ubuntu
```

And then you **must log out** and re-authenticate to your Ubuntu system.

After doing that, your `docker` commands should now succeed:

```{code-block} console
$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

You're now ready to get started on the lab!

## Terminology

A quick aside on terminology.

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

For more background, see docker's [What is a Container?](https://www.docker.com/resources/what-container/) page.

## Creating images

As described in [the terminology section](#terminology), images are bundles. Those bundles need to be created (or
"built"), and the primary way that we do that is by creating a `Dockerfile`. For instance:

```{code-block} bash
---
class: no-copybutton
---
FROM nginx
WORKDIR /
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
EXPOSE 80
```

In the above example, you see that we are starting with `FROM nginx`. This means two things:
1. We are implicitly using the special `latest` tag of `nginx` (see other available tags
   [here](https://hub.docker.com/_/nginx/tags)).
1. We are also implicitly pulling the images from Docker Hub, which is the default
   [Registry](https://docs.docker.com/registry/) for `docker`.

Based on these two items, `FROM nginx` is functionally equivalent to `FROM docker.io/nginx:latest`. This will be
important later.

### Unsafe default configurations

There are a myriad of ways a container or image can be insecure. In our example, the image we were just looking at above
does not define a `USER`:

```{code-block} console
---
emphasize-lines: 14
---
$ docker pull nginx
Using default tag: latest
latest: Pulling from library/nginx
26c5c85e47da: Pull complete
4f3256bdf66b: Pull complete
2019c71d5655: Pull complete
8c767bdbc9ae: Pull complete
78e14bb05fd3: Pull complete
75576236abf5: Pull complete
Digest: sha256:63b44e8ddb83d5dd8020327c1f40436e37a6fffd3ef2498a6204df23be6e7e94
Status: Downloaded newer image for nginx:latest
docker.io/library/nginx:latest
$ docker inspect nginx:latest | jq '.[].Config.User'
""
```

This configuration is unsafe, because when the user is empty or unspecified, it will default to using the `root` user.

Another way to check for the user in use is by running `whoami` while the container is running.

```{code-block} console
$ docker run nginx:latest whoami
root
```

```{note}
If you need to quickly scan a `Dockerfile` to find issues, I suggest [hadolint](https://github.com/hadolint/hadolint)
based on its out-of-the-box rules, and if you need more customized options I would look at
[conftest](https://www.conftest.dev/) from the Open Policy Agent (OPA) project (you can check out an example
`Dockerfile` policy [here](https://github.com/open-policy-agent/conftest/tree/master/examples/docker)).
```

### Changing the user

Running as `root` is not preferred, and although there are [ways to
secure](https://docs.docker.com/engine/security/userns-remap/) a process that must run as `root`, it should not be the
default. So, let's fix that.

We'll start by making a temporary working area:

```{code-block} console
$ newdir=$(mktemp -d)
$ pushd "${newdir}"
```

And then we create a `Dockerfile` that defines a more secure image. It starts with `FROM nginx`, meaning that we are
building on top of the upstream `nginx` image, inheriting all of its secure (or insecure) properties, and then adding
our changes on top.

```{code-block} bash
cat << EOF > Dockerfile
FROM nginx
RUN groupadd --gid 53150 -r notroot \
 && useradd -r -g notroot -s "\$(which bash)" --create-home --uid 53150 notroot
USER notroot
EOF
```

Now we can build the more secure image and examine it to see what the configured `User` is. Note the user on the last
line is _not_ the root user.

```{code-block} console
---
emphasize-lines: 17
---
$ docker buildx build -t example-secure .
[+] Building 1.0s (6/6) FINISHED
 => [internal] load build definition from Dockerfile                                                                             0.1s
 => => transferring dockerfile: 178B                                                                                             0.0s
 => [internal] load .dockerignore                                                                                                0.1s
 => => transferring context: 2B                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/nginx:latest                                                                  0.0s
 => [1/2] FROM docker.io/library/nginx                                                                                           0.1s
 => [2/2] RUN groupadd --gid 53150 -r notroot  && useradd -r -g notroot -s "$(which bash)" --create-home --uid 53150 notroot     0.5s
 => exporting to image                                                                                                           0.2s
 => => exporting layers                                                                                                          0.2s
 => => writing image sha256:4d20cb10ba62fdea186dae157c2f08980efba65de1e2b86f708da46847c62570                                     0.0s
 => => naming to docker.io/library/example-secure                                                                                0.0s
$ popd
~
$ docker inspect example-secure | jq -r '.[].Config.User'
notroot
```

Success!

You can also confirm that the container will not use the root user by default by running the container and checking the
current user.

```{code-block} console
$ docker run example-secure whoami
notroot
```

Does this mean it's impossible to run this container insecurely? Absolutely not! For instance, let's re-run that command
with one additional argument, asking it to use the `root` user explicitly.

```{code-block} console
$ docker run --user 0 example-secure whoami
root
```

All we've done is make a more secure configuration _the default_, not impossible. While this is a great start, further
securing your container runtimes requires a host of additional layers of security; what we generally refer to as Policy
as Code. Check back in the future for a lab on that 😀

```{seealso}
---
class: dropdown
---
Everything we've been doing so far has created docker images which are not OCI-compliant. This means they do not follow
the OCI Image specification.

This can lead to confusion in downstream use cases, when your runtime expects a given artifact structure.

If you'd like to use the `docker` command line to create an OCI-compliant output, you can run `docker buildx build -o
type=oci,dest=example.tar .`

However, this will not necessarily make it usable on your system. If you run a `docker load` to make `example.tar`
usable, it will no longer be OCI-compliant, so you will need to use a third party tool (such as `crane`) to push your
`example.tar` OCI-compliant image to a registry.
```

## Image signing

Now we have a (more) secure docker image called `example-secure`.

If we wanted to share this image so others could run it, we could `docker login` and then `docker push` it to the docker
hub registry (we don't do that in this lab, but if you'd like to, there are instructions
[here](https://docs.docker.com/get-started/04_sharing_app/)).

But, if we did that, how would the consumers of the image know that it came from us?

Ostensibly, only "we" have access to push images to the registry. But what if an attacker is able to compromise a set of
credentials that allows pushing a malicious image?

Enter image signing.

Similar to code signing, image signing allows us to create a cryptographic signature using a private key and then we can
"associate" it with the image (more on that later). Then, consumers of our images can verify the signature to ensure
that the person who pushed the image not only had sufficient access to push the image, but also access to our image
signing private key.

### Image signing setup

The most precise way to sign an image is to sign the digest, as opposed to a tag which can point to different versions
of an image over time. Let's retrieve the digest for our `example-secure` image:

```{code-block} console
$ docker inspect --format='{{index .RepoDigests 0}}' example-secure

template parsing error: template: :1:2: executing "" at <index .RepoDigests 0>: error calling index: reflect: slice
index out of range
```

Hmm, that didn't work. Let's try a couple other ways:

```{code-block} console
$ docker inspect --format='{{.RepoDigests}}' example-secure
[]
$ docker images --digests example-secure
REPOSITORY       TAG       DIGEST    IMAGE ID       CREATED       SIZE
example-secure   latest    <none>    cad64b88527f   2 hours ago   159MB
```

Well, it looks like we don't have an image digest 🤔

What we're seeing is another `docker` specific implementation detail. The digest will not be created for new images
until it is pushed to a registry (technically a v2 registry, which has been around since 2015), or if it was pulled
_from_ a v2 registry.

For example, the `nginx:latest` image that we pulled previously from docker hub does have an image digest:

```{code-block} console
$ docker inspect --format='{{index .RepoDigests 0}}' nginx
nginx@sha256:63b44e8ddb83d5dd8020327c1f40436e37a6fffd3ef2498a6204df23be6e7e94
```

```{note}
The actual SHA-256 digest that you receive may differ from the above. This is because the implicit `latest` tag is
updated over time to point to the latest released image, and is exactly why we sign digests instead of tags.

You are able to get the best of both worlds by combining the two approaches by adding a tag "annotation"; we'll cover
that more later.
```

However, we want our `example-secure` image to have a digest. We can fix this by running a v2 registry locally and then
pushing the image to it!

We'll start by setting up HTTPS, and then pulling down a registry image and running the container:

```{code-block} console
$ newdir=$(mktemp -d)
$ mkdir -p "${newdir}/certs"
$ pushd "${newdir}/certs"
/tmp/tmp.hzH6IxKkz2/certs ~
$ openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 60 -nodes -subj "/CN=registry"
Generating a RSA private key
....................................++++
..................................................................................................................................................................................................................++++
writing new private key to 'key.pem'
-----
$ docker run -d -p 443:443 --name registry -v "$(pwd)":/certs -e REGISTRY_HTTP_ADDR=0.0.0.0:443 -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/cert.pem -e REGISTRY_HTTP_TLS_KEY=/certs/key.pem registry:2

Unable to find image 'registry:2' locally
2: Pulling from library/registry
91d30c5bc195: Pull complete
65d52c8ad3c4: Pull complete
54f80cd081c9: Pull complete
ca8951d7f653: Pull complete
5ee46e9ce9b6: Pull complete
Digest: sha256:8c51be2f669c82da8015017ff1eae5e5155fcf707ba914c5c7b798fbeb03b50c
Status: Downloaded newer image for registry:2
fa830229c72a484fa1b1c18ffc9039712b2561d4aa5c8f7856ed00b3e275ed65
$ popd
~
```

Question: Do you know what `fa830229c72a484fa1b1c18ffc9039712b2561d4aa5c8f7856ed00b3e275ed65` is?

:::{admonition} Answer
---
class: dropdown hint
---
What we're seeing is not an image digest, but rather a container ID. This is a unique identifier that `docker` create
for each container. If you were to run the same command again, you will receive a different identifier, for instance:

```{code-block} bash
---
class: no-copybutton
emphasize-lines: 2
---
$ docker run -d -p 443:443 --name registry2 registry:2
892c9c6be865fe31007e6c30984983d0a02f9173501c93e4f801afaef42d5469
```

Note that now I received an ID starting with `892c9` whereas previously the same command gave an ID starting with `fa830`. You can see the container IDs for all of your running commands by running `docker ps` and examining the first column:

```{code-block} console
$ docker ps
CONTAINER ID   IMAGE        COMMAND                  CREATED          STATUS          PORTS                  NAMES
fa830229c72a   registry:2   "/entrypoint.sh /etc…"   15 minutes ago   Up 15 minutes   0.0.0.0:443->443/tcp   registry
```

However, you'll notice that the container ID is truncated. This truncation is to simplify the readability of the output.
If you'd like avoid truncation, add the `--no-trunc` option:

```{code-block} console
$ docker ps --no-trunc
CONTAINER ID                                                       IMAGE        COMMAND
CREATED          STATUS          PORTS                  NAMES
fa830229c72a484fa1b1c18ffc9039712b2561d4aa5c8f7856ed00b3e275ed65   registry:2   "/entrypoint.sh /etc/docker/registry/config.yml"      17 minutes ago   Up 17 minutes   0.0.0.0:443->443/tcp   registry
```

You'll noticed that the output is significantly longer and harder to read now, but it avoids any truncation.

If you'd like to interact with a running container, you can use this container ID, or the associated name (in my
example, `registry`). For instance:

```{code-block} console
$ docker exec fa8302 ps
PID   USER     TIME  COMMAND
    1 root      0:01 registry serve /etc/docker/registry/config.yml
   16 root      0:00 ps
$ docker exec registry ps
PID   USER     TIME  COMMAND
    1 root      0:01 registry serve /etc/docker/registry/config.yml
   22 root      0:00 ps
```

But wait, `fa8302` isn't the full container id, nor is it the one that `docker ps` showed me earlier, so what gives?

Well, `docker` has access to a full list of container IDs on your system, and so it allows you to provide the minimum
number of characters required to uniquely identify a container, for brevity. How convenient!
:::

Now that there's a registry running locally, we can push our `example-secure` image to it, but first we are going to
re-tag that image to include the registry information so it knows what destination to push _to_.

```{code-block} console
$ docker tag example-secure localhost:443/example-secure
```

Now, when we push the fully qualified tag, it will know to use the registry hosted locally, instead of the implicit
docker hub registry.

```{code-block} console
$ docker push localhost:443/example-secure
Using default tag: latest
The push refers to repository [localhost:443/example-secure]
cd561337639d: Pushed
579d9b6c655f: Pushed
ce6504827299: Pushed
cbd644319450: Pushed
7577f7ad3cd4: Pushed
4bdc748e7c3d: Pushed
c607b6f95cf7: Pushed
0b9f60fbcaf1: Pushed
latest: digest: sha256:5ebcdc0d0e56fc8ab8d7095e2107a830d4624b0044e66c8c4488130ec984d9ae size: 1985
```

And finally, we have an image digest! 🎉

```{code-block} console
$ docker inspect --format='{{index .RepoDigests 0}}' example-secure
localhost:443/example-secure@sha256:5ebcdc0d0e56fc8ab8d7095e2107a830d4624b0044e66c8c4488130ec984d9ae
```

### Image signing

Now that we have an image digest, we can properly sign the image. In order to perform our signing and validation
operations, we'll be using the `cosign` tool, which is an [Open Source Security Foundation](https://openssf.org/)
project under the [sigstore](https://www.sigstore.dev/) umbrella.

In order to sign the image, we will:

1. Pull another docker image that contains `cosign` (are you seeing the pattern yet? 😀)
1. Setup some docker networking so the `cosign` container can reach the `registry` container
1. Use the `cosign` container to generate an encrypted keypair
1. Sign the `example-secure` image using the private key
1. Verify the `example-secure` signature using the public key

We're also going to be using a number of new `docker` arguments below; if you'd
like to look into those futher, see the `docker run` documentation
[here](https://docs.docker.com/engine/reference/commandline/run/).

```{code-block} console
$ docker pull cgr.dev/chainguard/cosign
Using default tag: latest
latest: Pulling from chainguard/cosign
dc16c8d156c6: Pull complete
Digest: sha256:87bfbf14a15695c02f2e13cb636706f5936c7a6b344b915e269df352449bdb14
Status: Downloaded newer image for cgr.dev/chainguard/cosign:latest
cgr.dev/chainguard/cosign:latest
$ docker network create workshop
316fa415e729ff7f48319daf815e7e2842da09d76e948eb51b7d5823dec082ee
$ docker network connect workshop registry
$  export COSIGN_PASSWORD='example'
$ docker run -e COSIGN_PASSWORD -u 0 -v "$(pwd):/app" -w /app cgr.dev/chainguard/cosign generate-key-pair
$ image_digest="$(docker inspect --format='{{index .RepoDigests 0}}' localhost:443/example-secure | cut -f2 -d@)"
$ docker run -e COSIGN_PASSWORD -u 0 --network workshop -v "$(pwd):/app" -w /app cgr.dev/chainguard/cosign sign --yes --key cosign.key -a tag=latest registry:443/example-secure@"${image_digest}" --allow-insecure-registry

        The sigstore service, hosted by sigstore a Series of LF Projects, LLC, is provided pursuant to the Hosted Project Tools Terms of Use, available at https://lfprojects.org/policies/hosted-project-tools-terms-of-use/.
        Note that if your submission includes personal data associated with this signed artifact, it will be part of an immutable record.
        This may include the email address associated with the account with which you authenticate your contractual Agreement.
        This information will be used for signing this artifact and will be stored in public transparency logs and cannot be removed later, and is subject to the Immutable Record notice at https://lfprojects.org/policies/hosted-project-tools-immutable-records/.

By typing 'y', you attest that (1) you are not submitting the personal data of any other person; and (2) you understand and agree to the statement and the Agreement terms at the URLs listed above.
tlog entry created with index: 18622505
Pushing signature to: registry:443/example-secure
```

We've officially signed our `example-secure` image!

In the above command, we generated a public and private keypair, signed the latest image digest of the
`localhost:443/example-secure` image, and pushed that signature to our local registry to live alongside the image.

We also added an annotation of `tag` with the value of `latest` to describe what we are signing at the moment, which is
the `latest` tag. These annotations provide valuable additional context, and it is very common to add annotations such
as the `git` commit hash, details about the CI/CD pipeline that built and signed the image, etc.

```{note}
---
class: dropdown
---
Interested in skipping the `cosign generate-key-pair` step from above? You can, with what sigstore calls "keyless
signing". In reality, just like serverless isn't serverless, keyless also isn't keyless. It's just that you don't have
to generate or manage the keys yourself; they are created on the fly, tied to an OIDC identity, used to create a
short-lived certificate and to facilitate the signing process, and then securely erased.

To learn more, check out the `cosign sign` documentation for
[keyless](https://docs.sigstore.dev/cosign/sign/#keyless-signing).
```

```{note}
---
class: dropdown
---
Although the private key is encrypted, many secrets scanning tools don't have exclusions for encrypted cosign private
keys and will still flag them as insecure.

For instance, [gitleaks](https://github.com/gitleaks/gitleaks) (one of my favourite secret scanning tools) will flag an
encrypted cosign private key, and doesn't have a straightforward workaround due to the Go programming language's regex
library's choice not to support negative lookaheads (see the issue I opened on this
[here](https://github.com/gitleaks/gitleaks/issues/1034). The best approach in most cases, albeit imperfect, is to
exclude the specific `.key` file entirely.
```

:::{seealso}
---
class: dropdown
---
Technically, the above approach is not the most secure way to do this because it has a race condition. It requires that
an image be pushed prior to being signed, and has no way to accomodate signing failures.

However, there is not a great alternative right now. `docker` doesn't populate the repo digest until it's `docker
push`ed, and `cosign` also doesn't support a sign-then-push workflow.

There is an [issue open](https://github.com/sigstore/cosign/issues/1905) on the `cosign` project to fix this, feel free
to go subscribe to be notified of activity.
:::

Now, let's bring things full circle and verify the signature

```{code-block} console
$ docker run -e COSIGN_PASSWORD -u 0 --network workshop -v "$(pwd):/app" -w /app cgr.dev/chainguard/cosign verify --key cosign.pub registry:443/example-secure@"${image_digest}" --allow-insecure-registry

Verification for registry:443/example-secure@sha256:8f5a0b6ab1511420fc6e00d01ca5bc4c87bb49d631c95e12d254f8c4831134c9 --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key

[{"critical":{"identity":{"docker-reference":"registry:443/example-secure"},"image":{"docker-manifest-digest":"sha256:8f5a0b6ab1511420fc6e00d01ca5bc4c87bb49d631c95e12d254f8c4831134c9"},"type":"cosign container image signature"},"optional":{"Bundle":{"SignedEntryTimestamp":"MEQCIFaWevE2v/civ3rCVYkWda/wmx9n+cUy+gnzgDetDZ2jAiBEzPIy5bFwOBBj4+yqK/yzUlVXCNmNgkA8JgnsZjIyBA==","Payload":{"body":"eyJhcGlWZXJzaW9uIjoiMC4wLjEiLCJraW5kIjoiaGFzaGVkcmVrb3JkIiwic3BlYyI6eyJkYXRhIjp7Imhhc2giOnsiYWxnb3JpdGhtIjoic2hhMjU2IiwidmFsdWUiOiJmZjdhNmU0ODMwMDE0ZDFhMjUwZDA0MzUzY2UxNWZkNmY1NDExYTI5NDdmYmZkNmNlOTYzZmNmNmRmNjhhODQ4In19LCJzaWduYXR1cmUiOnsiY29udGVudCI6Ik1FUUNJRmVFdTRkdXU5UHhYSDFqWWZZRmFnUUUrWkYzTCs3TkJoTVozZG9qUEU5REFpQWs4Vm4rYmRkV2Q0YlRtV2lQckh0ZXJ5cHBXbC9BaVVST1RrV1kvdjh6WVE9PSIsInB1YmxpY0tleSI6eyJjb250ZW50IjoiTFMwdExTMUNSVWRKVGlCUVZVSk1TVU1nUzBWWkxTMHRMUzBLVFVacmQwVjNXVWhMYjFwSmVtb3dRMEZSV1VsTGIxcEplbW93UkVGUlkwUlJaMEZGYzJReVdXYzVNRGtySzBaRmF5dGpiak5zVmt4Q1MwWndaUzlvVGdwdmIwRmtZVkkxWmxOd2MzVTVUbVV3T1hJM2FYUXhhVXgzUm5oa05FVnFVRkZ6YTJsQ2VYaHpaa0ZzVldONFdqWmFPVUZpZUVJeVZsUkJQVDBLTFMwdExTMUZUa1FnVUZWQ1RFbERJRXRGV1MwdExTMHRDZz09In19fX0=","integratedTime":1682131706,"logIndex":18624203,"logID":"c0d23d6ad406973f9559f3ba2d1ca01f84147d8ffc5b8445c224f98b9591801d"}},"tag":"latest"}}]
$ echo $?
0
```

```{note}
---
class: dropdown
---
If you looked carefully, you may have seen the `--allow-insecure-registry` argument. This is only for our test
environment, where we are using a self-signed certificate for the registry. In production this should **not** ever be
used.
```

It worked!

And in addition, evidence of this signing process was added to a public, software supply chain transparency log called
rekor. Let's check it out!

```{code-block} console
$ curl https://rekor.sigstore.dev/api/v1/log/entries/24296fb24b8ad77ad9ca41820f93cdbef2264692ced5c142d19e2ba859ab9f2b500d1917afe8ef30
{"24296fb24b8ad77ad9ca41820f93cdbef2264692ced5c142d19e2ba859ab9f2b500d1917afe8ef30":{"body":"eyJhcGlWZXJzaW9uIjoiMC4wLjEiLCJraW5kIjoiaGFzaGVkcmVrb3JkIiwic3BlYyI6eyJkYXRhIjp7Imhhc2giOnsiYWxnb3JpdGhtIjoic2hhMjU2IiwidmFsdWUiOiJmZjdhNmU0ODMwMDE0ZDFhMjUwZDA0MzUzY2UxNWZkNmY1NDExYTI5NDdmYmZkNmNlOTYzZmNmNmRmNjhhODQ4In19LCJzaWduYXR1cmUiOnsiY29udGVudCI6Ik1FUUNJRmVFdTRkdXU5UHhYSDFqWWZZRmFnUUUrWkYzTCs3TkJoTVozZG9qUEU5REFpQWs4Vm4rYmRkV2Q0YlRtV2lQckh0ZXJ5cHBXbC9BaVVST1RrV1kvdjh6WVE9PSIsInB1YmxpY0tleSI6eyJjb250ZW50IjoiTFMwdExTMUNSVWRKVGlCUVZVSk1TVU1nUzBWWkxTMHRMUzBLVFVacmQwVjNXVWhMYjFwSmVtb3dRMEZSV1VsTGIxcEplbW93UkVGUlkwUlJaMEZGYzJReVdXYzVNRGtySzBaRmF5dGpiak5zVmt4Q1MwWndaUzlvVGdwdmIwRmtZVkkxWmxOd2MzVTVUbVV3T1hJM2FYUXhhVXgzUm5oa05FVnFVRkZ6YTJsQ2VYaHpaa0ZzVldONFdqWmFPVUZpZUVJeVZsUkJQVDBLTFMwdExTMUZUa1FnVUZWQ1RFbERJRXRGV1MwdExTMHRDZz09In19fX0=","integratedTime":1682131706,"logID":"c0d23d6ad406973f9559f3ba2d1ca01f84147d8ffc5b8445c224f98b9591801d","logIndex":18624203,"verification":{"inclusionProof":{"checkpoint":"rekor.sigstore.dev - 2605736670972794746\n14461401\nhiZ41EGZQqn3qWoXCV7NR4CET8Opt1BWZ56N5FsJuXQ=\nTimestamp: 1682132568542746071\n\n—  rekor.sigstore.dev  wNI9ajBFAiEAlXVguDvXhjyXnwjX0/D64F/nZesHWwJGCSaKyun0KlcCIEXq8yh7MN8BP0vW1aW/FYSBzV5fVwSJKd5NrOg75eaT\n","hashes":["76953dcdf1b59a3f682ee895bd4a4cb5868ee40a3d45ebf75bdc62adecdb2b4a","c8d6687d876151821b739a75821e111821e607743bf7a6f32e7681a2fa0c4501","7217c11743bfc97d1507f5681d9c3505b00e8d47ce7fcd90a8c2c14c51805e2e","7d6bde85aacb040500212f6567d81b4297a574377da748f378d439931f194247","b8f398cbfc968928b53974ea16c96c0ca4d61a222c1cc90ea24fd8ace57b07a1","1b1c51d9a3857dad776b8cae131ce9c4c17b8fb50a932bff58d33d5c0c8cd7b3","9db3f1057b4b0315360aa4d3225bc84c1855f223346337e32ee56db52b814084","44521e9d9f6a1b9c064b92d25c42a146488701f9e7787aa1f1a68a208d5edf64","deb3d900893c1871cdef5a234e770a60eb1b6fc507e8a5c35c3037f70bfbe4ce","d0103a677e2bf2598ba11017194e75fd86825dd4745dce2c0b247f90b7d3e92d","69d4cd1a5d76e4df7cc18552d76dce66d7d3c8c631241f49d23f5fd70f46f2f1","ba0e22b19049b1610e726a3481382451f37aabfc0c3606114918ebaec0e6b16e","3c9e72db0940d7be6cfaa67197efb5e3c48cdb96bd47b6afa8f621cc2790da5c","71e138a81c8b8e6871958ce12b747ef7e2c65ae1bfc9a5e0247734c7e372d899","3f7a2bb24688b2c4956a652ddba433123d92bba8cd565d880e2a9b871ea511e0","781de2e242cf8fe1432593030707a2e357e13c28632fc46ed3b158c9a1266fa1","ec4c6515563a676a411e44ad06b2df2dffda2c037787eeba00c95bc3b5345955","d63092c2277805dcb4cb361bea6e09ac7ed9e9e9192724b8f51e57e54bdf3531","9e040066dfe5f02004658386ac66cf0bb6ffe857ed71cb337c7f5545ecf4558b"],"logIndex":14460772,"rootHash":"862678d4419942a9f7a96a17095ecd4780844fc3a9b75056679e8de45b09b974","treeSize":14461401},"signedEntryTimestamp":"MEYCIQCyJq8dKr404aMxl8p5eNwDHHPh5+BF+jzmpOxCFYM3XgIhAOMkGSLCxUW9Wx5yhztUOANvFpyeXgS8GQlPgl9dSFXf"}}}
```

Well, that was a lot. If you'd like, you can also view the details in a web browser
[here](https://search.sigstore.dev/?logIndex=18624203).

```{admonition} Section wrap-up
---
class: hint
---
Today, the way that these signatures are hosted is that they are `in-toto`
[attestations](https://github.com/in-toto/attestation) bundled into OCI artifacts, and uploaded to a registry with a
specifically formatted name of `sha256:<DIGEST>.sig` where <DIGEST> is the image digest.

This works great because the registry only needs to support OCI artifacts, which most (effectively all) of them do, and
if you are running a container, you are always able to look up the digest of the related image.

Luckily, there is something better in the works here as well. Currently, the OCI
[image](https://github.com/opencontainers/image-spec) and
[distribution](https://github.com/opencontainers/distribution-spec) specifications have a release candidate for a
version 1.1 which will support "Reference Types", meaning that these signatures will be able to be directly attached to
a given OCI artifact.

Once this release is finalized, vendors providing registry software will need to update to support those new
specifications, and then update their hosted registries. The jury is out on how long that will take, but we can be
hopeful that it will come sooner rather than later 🤞

If you'd like more of an introduction to Reference Types, I recommend the chainguard blog
[here](https://www.chainguard.dev/unchained/intro-to-oci-reference-types).
```

## Vulnerability scanning images

### Approaches

SBOM generate-then-scan

Scan the image

Scan the repository

Why is scan the image better than repository?

TODO: Generate an SBOM with syft. Briefly cover CycloneDX and SPDX, as well as syft's proprietary format.

```{note}
---
class: dropdown
---
Changes to the code can happen during build, including bringing in new dependences, or different versions of known
dependencies.

While containers could technically also make those changes at runtime, it is significantly less popular and easier to
monitor for/prevent.
```

TODO: Examine the SBOM for `nginx`.

TODO: run grype on the `nginx` sbom.

Move to `cgr.dev/chainguard/nginx`, re-run the SBOM and grype, compare the results. Refer back to the implicit nginx
registry/tag from above.

Check for the chainguard signature. Nice! They have it. Consider cgr alternatives, supply chain, etc.

Now, what if you don't know what supply chain security information exists for a given image? There's a helper for that!

We can use the `cosign tree` command to "Display supply chain security related artifacts for an image such as
signatures, SBOMs and attestations". Let's take a look at what the `cgr.dev/chainguard/cosign` image that we've been
using to run `cosign` commands has available:

```{code-block} console
$ docker run cgr.dev/chainguard/cosign tree cgr.dev/chainguard/cosign
📦 Supply Chain Security Related artifacts for an image: cgr.dev/chainguard/cosign
└── 💾 Attestations for an image tag: cgr.dev/chainguard/cosign:sha256-d15e181a549c2086aebaeafcd731bf7daaae8f07f4bd45ec22520d75fb849085.att
   ├── 🍒 sha256:db7407d7255baa87a62874e548ad9c45dd71fd388b1cec2752e3c326ce122bd1
   ├── 🍒 sha256:56d78c3c69009365e9431221272f4a9ecc2f7e0cf510b82bd7e88b3bf265ebf0
   ├── 🍒 sha256:644c4d060943cab88b0b128188bbda049598dda413a5bdb610a3f2c3a959847a
   └── 🍒 sha256:30845e6bee8de3885d82fecdfdaa3755c1f30b07e2902a34c07651cb14594a7f
└── 🔐 Signatures for an image tag: cgr.dev/chainguard/cosign:sha256-d15e181a549c2086aebaeafcd731bf7daaae8f07f4bd45ec22520d75fb849085.sig
   └── 🍒 sha256:e5d73bd8602c35b5d0a33a095329ac63e4bc6dc3f03d83c7594cc9e317d5d4f0
└── 📦 SBOMs for an image tag: cgr.dev/chainguard/cosign:sha256-d15e181a549c2086aebaeafcd731bf7daaae8f07f4bd45ec22520d75fb849085.sbom
   └── 🍒 sha256:e5f7592e081e7e7ba55e2941e2ed1d324b0e62e7ce02e1052fcf7ebdee2d6445
```

Not bad! In addition to a signature and SBOM, there are 4 additional attestations available for this image that we could
use to evaluate and make policy decisions about whether or not we're comfortable using it in our environment.

## Container image components

High level explanation. manifests, indexes, and layers. Call back to signature process; what is actually being signed?
How does that work for multi-platform images?

Remember how we mentioned earlier that image signatures, vulnerability scan attestations, and other artifacts are
currently uploaded to a registry as separate OCI artifacts? Well, `crane` gives you a way to take a peek under the
covers and see those separate artifacts directly.

TODO: 1 paragraph background on crane. Example of where it's used?

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

## Read, Set, Break!

### Successful breakout

CAP_SYS_ADMIN? Mounted docker sock?

### Fix

### Failed breakout

## Container Breakout

## Conclusion

If you've made it this far, congratulations!

Looking for more content like this?

- Connect with me [on LinkedIn](https://linkedin.com/in/jonzeolla/)
- Check out SANS [SEC540 class](http://sans.org/sec540) for 5 days of Cloud Security and DevSecOps training

## Cleanup

Don't forget to stop or terminate your EC2 instance!
