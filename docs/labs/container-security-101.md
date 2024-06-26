# Container Security 101

Welcome to my Container Security 101 workshop!

Is your company adopting containers but you haven’t had a chance to figure out the best way to secure them yet? In this lab, we get hands-on with containers,
learn how to examine them for common mistakes, and then add in some security controls like container image signing, create a Software Bill of Materials, and run
vulnerability scans.

For some additional background and an introduction to the lab, check out this presentation.

<center><iframe width="560" height="315" src="https://www.youtube.com/embed/-iJbGBJTRyk" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></center>
<br />

```{note}
The above recording was a part of [this webcast](https://www.sans.org/webcasts/container-security-101/), sponsored by [SANS Cloud
Security](https://www.sans.org/cloud-security/). Thank you!
```

## Agenda

```{toctree}
---
caption: Agenda
maxdepth: 1
---
```

1. [Create secure and insecure container images](creating-images)
1. [Perform container image signing](image-signing)
1. [Create SBOMs](making-a-software-bill-of-materials)
1. [Vulnerability scan the images](vulnerability-scanning-images)

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
docker run --network host -v /:/host jonzeolla/labs:container-security-101
```

You're now ready to get started on the lab!

## Terminology

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

For more background, see docker's [What is a Container?](https://www.docker.com/resources/what-container/) page.

## Creating images

As described in [the terminology section](terminology), images are bundles. Those bundles need to be created (or "built"), and the primary way that we do that
is by creating a `Dockerfile`. For instance:

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
1. We are implicitly using the special `latest` tag of `nginx` (see other available tags [here](https://hub.docker.com/_/nginx/tags)).
1. We are also implicitly pulling the images from Docker Hub, which is the default [Registry](https://docs.docker.com/registry/) for `docker`.

Based on these two items, `FROM nginx` is functionally equivalent to `FROM docker.io/nginx:latest`. This will be important later.

### Unsafe default configurations

There are a myriad of ways a container or image can be insecure. In our example, the image we were just looking at above does not define a `USER`:

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
If you need to quickly scan a `Dockerfile` to find issues, I suggest [hadolint](https://github.com/hadolint/hadolint) based on its out-of-the-box rules, and if
you need more customized options I would look at [conftest](https://www.conftest.dev/) from the Open Policy Agent (OPA) project (you can check out an example
`Dockerfile` policy [here](https://github.com/open-policy-agent/conftest/tree/master/examples/docker)).
```

### Changing the user

Running as `root` is not preferred, and although there are [ways to secure](https://docs.docker.com/engine/security/userns-remap/) a process that must run as
`root`, it should not be the default. So, let's fix that.

We'll start by creating a `Dockerfile` that defines a more secure image. It starts with `FROM nginx`, meaning that we are building on top of the upstream
`nginx` image, inheriting all of its secure (or insecure) properties, and then adding our changes on top.

```{code-block} bash
cat << HEREDOC > Dockerfile
FROM nginx
RUN groupadd --gid 53150 -r notroot && useradd -r -g notroot -s "/bin/bash" --create-home --uid 53150 notroot
USER notroot
HEREDOC
```

Then we can build the more secure image and examine it to see what the configured `User` is. Note the user on the last line is _not_ the root user.

```{code-block} console
---
emphasize-lines: 15
---
$ docker buildx build -t example-secure .
[+] Building 1.0s (6/6) FINISHED
 => [internal] load build definition from Dockerfile                                                                             0.1s
 => => transferring dockerfile: 178B                                                                                             0.0s
 => [internal] load .dockerignore                                                                                                0.1s
 => => transferring context: 2B                                                                                                  0.0s
 => [internal] load metadata for docker.io/library/nginx:latest                                                                  0.0s
 => [1/2] FROM docker.io/library/nginx                                                                                           0.1s
 => [2/2] RUN groupadd --gid 53150 -r notroot  && useradd -r -g notroot -s "/bin/bash" --create-home --uid 53150 notroot         0.5s
 => exporting to image                                                                                                           0.2s
 => => exporting layers                                                                                                          0.2s
 => => writing image sha256:4d20cb10ba62fdea186dae157c2f08980efba65de1e2b86f708da46847c62570                                     0.0s
 => => naming to docker.io/library/example-secure                                                                                0.0s
$ docker inspect example-secure | jq -r '.[].Config.User'
notroot
```

Success!

You can also confirm that the container will not use the root user by default by running the container and checking the current user.

```{code-block} console
$ docker run example-secure whoami
notroot
```

Does this mean it's impossible to run this container insecurely? Absolutely not! For instance, let's re-run that command with one additional argument, asking it
to use the `root` user explicitly.

```{code-block} console
$ docker run --user 0 example-secure whoami
root
```

All we've done is make a more secure configuration _the default_, not impossible. While this is a great start, further securing your container runtimes requires
a host of additional layers of security; what we generally refer to as Policy as Code. Check back in the future for a lab on that 😀

```{seealso}
---
class: dropdown
---
Everything we've been doing so far has created docker images which are functional, but not OCI-compliant. This means they do not follow the OCI Image
specification.

This can lead to confusion in downstream use cases, when your runtime expects a given artifact structure.

If you'd like to use the `docker` command line to create an OCI-compliant output, you can run `docker buildx build -o type=oci,dest=example.tar .`

However, this will not necessarily make it usable on your system. If you run a `docker load` to make `example.tar` usable, it will no longer be OCI-compliant,
so you will need to use a third party tool (such as `crane`) to push your `example.tar` OCI-compliant image to a registry.
```

## Image signing

Now we have a (more) secure docker image called `example-secure`.

If we wanted to share this image so others could run it, we could `docker login` and then `docker push` it to the docker hub registry (we don't do that in this
lab, but if you'd like to, there are instructions [here](https://docs.docker.com/get-started/04_sharing_app/)).

But, if we did that, how would the consumers of the image know that it came from us?

Ostensibly, only "we" have access to push images to the registry. But what if an attacker is able to compromise a set of credentials that allows pushing a
malicious image?

Enter image signing.

Similar to code signing, image signing allows us to create a cryptographic signature using a private key and then we can "associate" it with the image (more on
that later). Then, consumers of our images can verify the signature to ensure that the person who pushed the image not only had sufficient access to push the
image, but also access to our image signing private key.

### Image signing setup

The most precise way to sign an image is to sign the digest, as opposed to a tag (e.g. `latest`) which can point to different versions of an image over time.
Let's retrieve the digest for our `example-secure` image:

```{code-block} console
$ docker inspect --format='{{index .RepoDigests 0}}' example-secure || true

template parsing error: template: :1:2: executing "" at <index .RepoDigests 0>: error calling index: reflect: slice index out of range
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

What we're seeing is another `docker` specific implementation detail. The digest will not be created for new images until it is pushed to a registry
(technically we must use the _manifest_ digest, and a v2 registry), or if it was pulled _from_ a v2 registry.

For example, the `nginx:latest` image that we pulled previously from docker hub does have an image digest:

```{code-block} console
$ docker inspect --format='{{index .RepoDigests 0}}' nginx
nginx@sha256:63b44e8ddb83d5dd8020327c1f40436e37a6fffd3ef2498a6204df23be6e7e94
```

```{note}
The actual SHA-256 digest that you receive may differ from the above. This is because the implicit `latest` tag is updated over time to point to the latest
released image, and is exactly why we sign digests instead of tags.

You are able to get the best of both worlds by combining the two approaches and adding the tag as an "annotation" (which we will do later).
```

However, we want our `example-secure` image to have a digest. We can fix this by running a v2 registry locally and then pushing the image to it!

We'll start by setting up HTTPS, and then pulling down a registry image and running the container.

```{note}
If you look closely, you'll notice the use of a "dummy" container below; this is being used to load files into a volume and is a well known
[work-around](https://github.com/moby/moby/issues/25245#issuecomment-365980572) for a feature that can be voted for
[here](https://github.com/docker/cli/issues/1436).
```

```{code-block} console
$ newdir=$(mktemp -d)
$ mkdir -p "${newdir}/certs"
$ pushd "${newdir}/certs"
/tmp/tmp.hzH6IxKkz2/certs ~
$ docker volume create workshop-certs
workshop-certs
$ docker container create --name dummy -v workshop-certs:/certs registry:2

Unable to find image 'registry:2' locally
2: Pulling from library/registry
91d30c5bc195: Pull complete
65d52c8ad3c4: Pull complete
54f80cd081c9: Pull complete
ca8951d7f653: Pull complete
5ee46e9ce9b6: Pull complete
Digest: sha256:8c51be2f669c82da8015017ff1eae5e5155fcf707ba914c5c7b798fbeb03b50c
Status: Downloaded newer image for registry:2
26d8c595ffd35fe4b8a0797533cf7c9749f93bbd0d66baa960f86ea75618661b
$ openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -sha256 -days 60 -nodes -subj "/CN=registry"
Generating a RSA private key
....................................++++
..................................................................................................................................................................................................................++++
writing new private key to 'key.pem'
-----
$ docker cp cert.pem dummy:/certs/cert.pem
Successfully copied 3.58kB to dummy:/certs/cert.pem
$ docker cp key.pem dummy:/certs/key.pem
Successfully copied 5.12kB to dummy:/certs/key.pem
$ docker run -d -p 443:443 --name registry -v workshop-certs:/certs -e REGISTRY_HTTP_ADDR=0.0.0.0:443 -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/cert.pem -e REGISTRY_HTTP_TLS_KEY=/certs/key.pem registry:2
fa830229c72a484fa1b1c18ffc9039712b2561d4aa5c8f7856ed00b3e275ed65
$ popd
~
```

Question: Do you know what `fa830229c72a484fa1b1c18ffc9039712b2561d4aa5c8f7856ed00b3e275ed65` is?

:::{admonition} Answer
---
class: dropdown hint
---
What we're seeing is not an image digest, but rather a container ID. This is a unique identifier that `docker` creates for each container. If you were to run
the same command again, you will receive a different identifier, for instance:

```{code-block} bash
---
class: no-copybutton
emphasize-lines: 2
---
$ docker run -d -p 443:443 --name registry2 registry:2
892c9c6be865fe31007e6c30984983d0a02f9173501c93e4f801afaef42d5469
```

Note that now I received an ID starting with `892c9` whereas previously the same command gave an ID starting with `fa830`. You can see the container IDs for all
of your running commands by running `docker ps` and examining the first column:

```{code-block} console
$ docker ps
CONTAINER ID   IMAGE        COMMAND                  CREATED          STATUS          PORTS                  NAMES
fa830229c72a   registry:2   "/entrypoint.sh /etc…"   15 minutes ago   Up 15 minutes   0.0.0.0:443->443/tcp   registry
```

However, you'll notice that the container ID is truncated. This truncation is to simplify the readability of the output. If you'd like avoid truncation, add the
`--no-trunc` option:

```{code-block} console
$ docker ps --no-trunc
CONTAINER ID                                                       IMAGE        COMMAND
CREATED          STATUS          PORTS                  NAMES
fa830229c72a484fa1b1c18ffc9039712b2561d4aa5c8f7856ed00b3e275ed65   registry:2   "/entrypoint.sh /etc/docker/registry/config.yml"      17 minutes ago   Up 17 minutes   0.0.0.0:443->443/tcp   registry
```

You'll notice that the output is significantly longer and harder to read now, but it avoids any truncation.

If you'd like to interact with a running container, you can use this container ID, or the associated name (in my example, `registry`). For instance, here we use
the container ID (which will be different in your case):

```{code-block} console
---
class: no-copybutton
---
$ docker exec fa8302 ps
PID   USER     TIME  COMMAND
    1 root      0:01 registry serve /etc/docker/registry/config.yml
   16 root      0:00 ps
```

And here we use the name to accomplish the same thing:

```{code-block} console
$ docker exec registry ps
PID   USER     TIME  COMMAND
    1 root      0:01 registry serve /etc/docker/registry/config.yml
   22 root      0:00 ps
```

But wait, `fa8302` isn't the full container id, nor is it the one that `docker ps` showed me earlier, so what gives?

Well, `docker` has access to a full list of container IDs on your system, and so it allows you to provide the minimum number of characters required to uniquely
identify a container, for brevity. How convenient!
:::

Now that there's a registry running locally, we can push our `example-secure` image to it, but first we are going to re-tag that image to include the registry
information so it knows what destination to push _to_.

```{code-block} console
$ docker tag example-secure localhost:443/example-secure
```

Now, when we push the fully qualified image name, it will know to use the registry hosted locally, instead of the implicit docker hub registry.

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

Now that we have an image digest, we can properly sign the image. In order to perform our signing and validation operations, we'll be using the `cosign` tool,
which is an [Open Source Security Foundation](https://openssf.org/) project under the [sigstore](https://www.sigstore.dev/) umbrella.

```{note}
---
class: dropdown
---
Although we use `cosign` in this lab, it is not the only option for performing image signing. Other options include:
1. CNCF [Notary project](https://notaryproject.dev/) and the associated [Notation](https://github.com/notaryproject/notation/) specification, which has been
   adopted by [AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/image-signing-steps.html) and [Azure Key
   Vault](https://learn.microsoft.com/en-us/azure/container-registry/container-registry-tutorial-sign-build-push).
1. [OpenPubkey](https://www.docker.com/blog/signing-docker-official-images-using-openpubkey/), which was announced at DockerCon 2023 and is described well in
   [this](https://www.docker.com/blog/signing-docker-official-images-using-openpubkey/) blog post (for additional details, see a detailed OpenPubkey paper
   [here](https://eprint.iacr.org/2023/296.pdf)).
1. Google's [Binary Authorization](https://cloud.google.com/binary-authorization/docs/key-concepts) format, which often includes various attestations, such as
   provenance details, evidence of manual assessments, and vulnerability scanning, based on the
   [kritis](https://github.com/grafeas/kritis/blob/master/docs/binary-authorization.md) specification.
```

In order to sign the image, we will:

1. Pull another docker image that contains `cosign` (are you seeing the pattern yet? 😀)
1. Setup some docker networking so the `cosign` container can reach the `registry` container
1. Use the `cosign` container to generate an encrypted keypair
1. Sign the `example-secure` image using the private key
1. Verify the `example-secure` signature using the public key

We're also going to be using a number of new `docker` arguments below; if you'd like to look into those further, see the `docker` cli documentation
[here](https://docs.docker.com/engine/reference/commandline/cli/).

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
$ docker run -e COSIGN_PASSWORD -u 0 --network workshop -v "$(pwd):/app" -w /app cgr.dev/chainguard/cosign generate-key-pair
$ image_digest="$(docker inspect --format='{{index .RepoDigests 0}}' localhost:443/example-secure | cut -f2 -d@ )"
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

In the above command, we generated a public and private keypair, signed the manifest digest of the `localhost:443/example-secure` image, and pushed that
signature to our local registry to live alongside the image.

We also added an annotation of `tag` with the value of `latest` to describe what we are signing at the moment, which is the `latest` tag. These annotations
provide valuable additional context, and it is very common to add annotations such as the `git` commit hash, details about the CI/CD pipeline that built and
signed the image, etc.

```{note}
---
class: dropdown
---
Interested in skipping the `cosign generate-key-pair` step from above? You can, with what sigstore calls "keyless signing". In reality, just like serverless
isn't serverless, keyless also isn't keyless. It's just that you don't have to generate or manage the keys yourself; they are created on the fly, tied to an
OIDC identity, used to create a short-lived certificate and to facilitate the signing process, and then securely erased.

To learn more, check out the [keyless documentation](https://docs.sigstore.dev/signing/overview/) and [Life of a Sigstore
Signature](https://www.youtube.com/watch?v=DrHrkSsozB0) presentation at SigstoreCon NA 2022 (slides
[here](https://static.sched.com/hosted_files/sigstoreconna22/f1/Life%20of%20a%20Sigstore%20Signature.pdf) and [this related blog
post](https://www.chainguard.dev/unchained/life-of-a-sigstore-signature)).
```

```{note}
---
class: dropdown
---
Although the private key is encrypted, many secret scanning tools don't have exclusions for encrypted cosign private keys and will still flag them as insecure.

For instance, [gitleaks](https://github.com/gitleaks/gitleaks) (one of my favourite secret scanning tools) will flag an encrypted cosign private key, and
doesn't have a straightforward workaround due to the Go programming language's regex library's choice not to support negative lookaheads (see the issue I opened
on this [here](https://github.com/gitleaks/gitleaks/issues/1034)). The best approach in most cases, albeit imperfect, is to exclude the specific `.key` file
from your secret scanning tool.
```

:::{seealso}
---
class: dropdown
---
Technically, the above approach is not the most secure way to do this because it has a race condition. It requires that an image be pushed prior to being
signed, and has no way to accommodate signing failures.

However, there is not a great alternative right now. `docker` doesn't populate the repo digest until it's `docker push`ed, and `cosign` also doesn't support a
sign-then-push workflow.

There is an [issue open](https://github.com/sigstore/cosign/issues/1905) on the `cosign` project to fix this, feel free to go subscribe to be notified of
activity.
:::

Now, let's bring things full circle and verify the signature

```{code-block} console
$  export COSIGN_PASSWORD='example'
$ image_digest="$(docker inspect --format='{{index .RepoDigests 0}}' localhost:443/example-secure | cut -f2 -d@ )"
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
If you looked carefully, you may have seen the `--allow-insecure-registry` argument. This is only for our test environment, where we are using a self-signed
certificate for the registry. In production this should **not** ever be used.
```

It worked!

And in addition, evidence of this signing process was added to a public, software supply chain transparency log called rekor. Let's check out an example
signature that I did previously, following these same steps:

```{code-block} console
$ curl https://rekor.sigstore.dev/api/v1/log/entries/24296fb24b8ad77ad9ca41820f93cdbef2264692ced5c142d19e2ba859ab9f2b500d1917afe8ef30
{"24296fb24b8ad77ad9ca41820f93cdbef2264692ced5c142d19e2ba859ab9f2b500d1917afe8ef30":{"body":"eyJhcGlWZXJzaW9uIjoiMC4wLjEiLCJraW5kIjoiaGFzaGVkcmVrb3JkIiwic3BlYyI6eyJkYXRhIjp7Imhhc2giOnsiYWxnb3JpdGhtIjoic2hhMjU2IiwidmFsdWUiOiJmZjdhNmU0ODMwMDE0ZDFhMjUwZDA0MzUzY2UxNWZkNmY1NDExYTI5NDdmYmZkNmNlOTYzZmNmNmRmNjhhODQ4In19LCJzaWduYXR1cmUiOnsiY29udGVudCI6Ik1FUUNJRmVFdTRkdXU5UHhYSDFqWWZZRmFnUUUrWkYzTCs3TkJoTVozZG9qUEU5REFpQWs4Vm4rYmRkV2Q0YlRtV2lQckh0ZXJ5cHBXbC9BaVVST1RrV1kvdjh6WVE9PSIsInB1YmxpY0tleSI6eyJjb250ZW50IjoiTFMwdExTMUNSVWRKVGlCUVZVSk1TVU1nUzBWWkxTMHRMUzBLVFVacmQwVjNXVWhMYjFwSmVtb3dRMEZSV1VsTGIxcEplbW93UkVGUlkwUlJaMEZGYzJReVdXYzVNRGtySzBaRmF5dGpiak5zVmt4Q1MwWndaUzlvVGdwdmIwRmtZVkkxWmxOd2MzVTVUbVV3T1hJM2FYUXhhVXgzUm5oa05FVnFVRkZ6YTJsQ2VYaHpaa0ZzVldONFdqWmFPVUZpZUVJeVZsUkJQVDBLTFMwdExTMUZUa1FnVUZWQ1RFbERJRXRGV1MwdExTMHRDZz09In19fX0=","integratedTime":1682131706,"logID":"c0d23d6ad406973f9559f3ba2d1ca01f84147d8ffc5b8445c224f98b9591801d","logIndex":18624203,"verification":{"inclusionProof":{"checkpoint":"rekor.sigstore.dev - 2605736670972794746\n14461401\nhiZ41EGZQqn3qWoXCV7NR4CET8Opt1BWZ56N5FsJuXQ=\nTimestamp: 1682132568542746071\n\n—  rekor.sigstore.dev  wNI9ajBFAiEAlXVguDvXhjyXnwjX0/D64F/nZesHWwJGCSaKyun0KlcCIEXq8yh7MN8BP0vW1aW/FYSBzV5fVwSJKd5NrOg75eaT\n","hashes":["76953dcdf1b59a3f682ee895bd4a4cb5868ee40a3d45ebf75bdc62adecdb2b4a","c8d6687d876151821b739a75821e111821e607743bf7a6f32e7681a2fa0c4501","7217c11743bfc97d1507f5681d9c3505b00e8d47ce7fcd90a8c2c14c51805e2e","7d6bde85aacb040500212f6567d81b4297a574377da748f378d439931f194247","b8f398cbfc968928b53974ea16c96c0ca4d61a222c1cc90ea24fd8ace57b07a1","1b1c51d9a3857dad776b8cae131ce9c4c17b8fb50a932bff58d33d5c0c8cd7b3","9db3f1057b4b0315360aa4d3225bc84c1855f223346337e32ee56db52b814084","44521e9d9f6a1b9c064b92d25c42a146488701f9e7787aa1f1a68a208d5edf64","deb3d900893c1871cdef5a234e770a60eb1b6fc507e8a5c35c3037f70bfbe4ce","d0103a677e2bf2598ba11017194e75fd86825dd4745dce2c0b247f90b7d3e92d","69d4cd1a5d76e4df7cc18552d76dce66d7d3c8c631241f49d23f5fd70f46f2f1","ba0e22b19049b1610e726a3481382451f37aabfc0c3606114918ebaec0e6b16e","3c9e72db0940d7be6cfaa67197efb5e3c48cdb96bd47b6afa8f621cc2790da5c","71e138a81c8b8e6871958ce12b747ef7e2c65ae1bfc9a5e0247734c7e372d899","3f7a2bb24688b2c4956a652ddba433123d92bba8cd565d880e2a9b871ea511e0","781de2e242cf8fe1432593030707a2e357e13c28632fc46ed3b158c9a1266fa1","ec4c6515563a676a411e44ad06b2df2dffda2c037787eeba00c95bc3b5345955","d63092c2277805dcb4cb361bea6e09ac7ed9e9e9192724b8f51e57e54bdf3531","9e040066dfe5f02004658386ac66cf0bb6ffe857ed71cb337c7f5545ecf4558b"],"logIndex":14460772,"rootHash":"862678d4419942a9f7a96a17095ecd4780844fc3a9b75056679e8de45b09b974","treeSize":14461401},"signedEntryTimestamp":"MEYCIQCyJq8dKr404aMxl8p5eNwDHHPh5+BF+jzmpOxCFYM3XgIhAOMkGSLCxUW9Wx5yhztUOANvFpyeXgS8GQlPgl9dSFXf"}}}
```

```{admonition} What's Rekor?
---
class: seealso
---
[Rekor](https://docs.sigstore.dev/logging/overview/) is one of the primary components of the Sigstore project. It aims to provide an immutable, tamper-resistant
ledger of metadata generated within a software project’s supply chain, similar to [Certificate Transparency](https://certificate.transparency.dev/).

By default, and as we saw previously, cosign will publish evidence of your signature operations to a hosted instance of Rekor at rekor.sigstore.dev for
independent validation and transparency.

If you'd prefer not to upload signing details to Rekor, you can pass `--tlog-upload=false` during `cosign sign`.
```

Well, that returned a lot of _stuff_. If you'd like, you can also view the details in a web browser
[here](https://search.sigstore.dev/?logIndex=18624203).

```{admonition} Storing Image Signatures
---
class: seealso
---
These signatures are bundled into OCI artifacts, and uploaded to a registry with a specifically formatted name of `sha256-<DIGEST>.sig` where `<DIGEST>` is the
image digest.

This works great because the registry only needs to support OCI artifacts, which most (effectively all) of them do, and if you are running a container, you are
always able to look up the digest of the related image.

Luckily, there is something better in the works here as well. Currently, the OCI [image](https://github.com/opencontainers/image-spec) and
[distribution](https://github.com/opencontainers/distribution-spec) specifications have a release candidate for a version 1.1 which will support "Reference
Types", meaning that these signatures will be able to be directly attached to a given OCI artifact.

Once this release is finalized, vendors providing registry software will need to update to support those new specifications, and then update their hosted
registries. The jury is out on how long that will take, but we can be hopeful that it will come sooner rather than later 🤞

These Reference Types provide a way to describe and query artifacts in a registry. It does this by introducing `artifact.manifest` "mediaTypes", to the existing
`image.manifest` and `image.index` "mediaTypes", along some other changes (such as replacing layers with "blobs" and creating an "artifactType" field).

This new metadata allows attestations, such as [these in-toto Attestation Predicates](https://github.com/in-toto/attestation/tree/main/spec/predicates), to be
stored as OCI Artifacts with added links (aka "manifests") which point from the artifact to an `image.manifest` (i.e. an individual OCI artifact containing an
image).

To learn more about this, I recommend Brandon Mitchell's [CloudNativeSecurityCon NA 2023 presentation](https://www.youtube.com/watch?v=_c1OdmP9Ssg)
presentation. If you'd like some more technical details, see Steve Lasker's [Container Plumbing Days 2021](https://www.youtube.com/watch?v=CxrTQnjlOsU) however
keep in mind that this presentation was given **years** before the specification was finalized.
```

## Making a Software Bill of Materials

Now that we have a docker image, we want to have a structured way to know what's in it, and if there are any vulnerabilities that may need tending to. There are
a few different approaches we can take here, but the most modern (and increasingly popular) is to generate a Software Bill of Materials (SBOM), and then assess
that SBOM artifact for issues.

This is effectively how Software Composition Analysis (SCA) tools have worked for years, except that we're now uniformly using standard formats for determining
software composition, such as [SPDX](https://spdx.dev/) and [CycloneDX](https://cyclonedx.org/), which are meant for information exchange (such as between
vendors and software consumers). SBOMs can also support enrichment through specifications like
[VEX](https://www.ntia.gov/files/ntia/publications/vex_one-page_summary.pdf) (see the nitty gritty on VEX
[here](https://docs.oasis-open.org/csaf/csaf/v2.0/csd01/csaf-v2.0-csd01.html#45-profile-5-vex) and a recent more opinionated specification called OpenVEX
[here](https://github.com/openvex/spec/blob/main/OPENVEX-SPEC.md)).

Let's get started by creating an SBOM with a popular generation tool, [`syft`](https://github.com/anchore/syft):

```{code-block} console
$ docker run -v "$(pwd):/tmp" -v /var/run/docker.sock:/var/run/docker.sock anchore/syft:latest docker:example-secure -o json --file example-secure.sbom.json
Unable to find image 'anchore/syft:latest' locally
latest: Pulling from anchore/syft
b5dc3672f171: Pull complete
46399d889351: Pull complete
05b8cdb378a3: Pull complete
Digest: sha256:ffde5d9aa0468a9bd7761330e585a8a9050fda7ae6a5fa070a29f4a6f922088a
Status: Downloaded newer image for anchore/syft:latest
$ ls -sh example-secure.sbom.json
2.5M example-secure.sbom.json
$ jq '.artifacts | length' < example-secure.sbom.json
143
```

```{note}
---
class: dropdown
---
This SBOM may not show _exactly_ what ends up running in production.

While dependencies are typically downloaded at build time, processes in containers could technically also download additional dependencies or make other changes
at runtime. In practice, it is significantly less popular and easier to monitor for/prevent, but something to be aware of.
```

This will create a new file, `example-secure.sbom.json` containing an SBOM of what it was able to find in our `example-secure` image, identifying 143 (!?!)
different artifacts. Think that our 160MB container only had `nginx` in it? Think again!

You also may be asking, which of the above standard SBOM formats did this output in? Great question; and the answer is none of the above. When you run with the
`json` output format (like we just did) `syft` uses a proprietary SBOM format to "get as much information out of Syft as possible!"

## Vulnerability scanning images

Now, why did we use the `json` output format for our SBOM? Well, in this case we would like to pass this SBOM file into another tool called
[`grype`](https://github.com/anchore/grype) to do some vulnerability scanning. Since both tools are developed and maintained by Anchore, you can see why this
format is the _only_ SBOM format which is supported to do a `grype` scan.

```{code-block} console
$ docker run -v "$(pwd):/tmp" anchore/grype sbom:example-secure.sbom.json --output json --file example-secure.vulns.json
Unable to find image 'anchore/grype:latest' locally
latest: Pulling from anchore/grype
3d4811e75147: Pull complete
657b6e8ab91d: Pull complete
e58480bec473: Pull complete
Digest: sha256:9d326e7fc0e4914481a2b0c458a0eb0891b04d00569a6f92bdc549507f2089a0
Status: Downloaded newer image for anchore/grype:latest
Report written to "example-secure.vulns.json"
$ ls -sh example-secure.vulns.json
528K example-secure.vulns.json
$ jq '.matches | length' < example-secure.vulns.json
144
```

In this example we can see that this container has 144 vulnerabilities of various severities.

Now that we know what we know about `nginx`, let's take a look at an alternative container which also contains a functional `nginx` binary, but brings along
with it fewer accessories (i.e. attack surface).

One newer alternative are the chainguard images, built on [wolfi](https://www.chainguard.dev/unchained/introducing-wolfi-the-first-linux-un-distro), which are
meant to be free, minimal, secure-by-default, and heavily maintained images that provide a secure foundation for others to build on top of.

Let's re-run our SBOM generation and vulnerability scan steps from before, but this time against the `cgr.dev/chainguard/nginx` version of `nginx`:

```{code-block} console
$ docker run -v "$(pwd):/tmp" -v /var/run/docker.sock:/var/run/docker.sock anchore/syft:latest docker:cgr.dev/chainguard/nginx -o json --file chainguard-nginx.sbom.json
$ ls -sh chainguard-nginx.sbom.json
140K chainguard-nginx.sbom.json
$ jq '.artifacts | length' < chainguard-nginx.sbom.json
26
$ docker run -v "$(pwd):/tmp" anchore/grype sbom:chainguard-nginx.sbom.json --output json --file chainguard-nginx.vulns.json
[0000]  WARN unknown relationship type: described-by form-lib=syft
<repeated warnings removed for brevity>
[0000]  WARN unknown relationship type: described-by form-lib=syft
Report written to "chainguard-nginx.vulns.json"
$ ls -sh chainguard-nginx.vulns.json
8.0K chainguard-nginx.vulns.json
$ jq '.matches | length' < chainguard-nginx.vulns.json
0
```

Huh, 0 vulnerabilities; did it even work?

Or at least, that's where my mind goes when I see something _so_ extreme.

But, that's actually by design. Chainguard is so proud of their consistently low vulnerabilities that they provide an [interactive
graph](https://visualization-ui.chainguard.app/bar?left=nginx%3alatest&right=cgr.dev%2fchainguard%2fnginx%3alatest) that you can use to compare the
`nginx:latest` findings to the `cgr.dev/chainguard/nginx:latest` findings (at least according to [Trivy](https://github.com/aquasecurity/trivy), another popular
docker image vulnerability scanning tool).

```{note}
Worried about those "unknown relationship type" errors? I was too, until I found [this issue](https://github.com/anchore/grype/issues/1244) describing that this
is due to new information coming from `syft` that `grype` hasn't been updated to be able to make use of yet. If you're running this lab and not seeing those
issues, it means that `grype` has had a release and is now in sync with the `syft` outputs.
```

I wonder, do we even need our `example-secure` image from before? Let's quickly check the user of this new `nginx`
image:

```{code-block} console
$ docker inspect cgr.dev/chainguard/nginx:latest | jq -r '.[].Config.User'
65532
```

Well, that's definitely not the `root` user (UID 0)! 🎉

It seems like this may be one good option (of numerous) that we could build on top of.

All of this analysis is really just a start, and if you are looking for a new image to build on top of, you likely would have more questions to ask before you
have enough information to make a decision.

To get you pointed in the right direction for some additional investigation, you can use the `cosign tree` command to "Display supply chain security related
artifacts for an image such as signatures, SBOMs and attestations". Let's take a look at what else the `cgr.dev/chainguard/nginx` image has available:

```{code-block} console
$ docker run cgr.dev/chainguard/cosign tree cgr.dev/chainguard/nginx
📦 Supply Chain Security Related artifacts for an image: cgr.dev/chainguard/nginx
└── 💾 Attestations for an image tag: cgr.dev/chainguard/nginx:sha256-475b56541eec5bf8ef725c8e8912dc1451e01d6065f0ceac7f6a39cb229fcfe2.att
   ├── 🍒 sha256:428c41b65c98785fdaa1ebcd2169851c9717ead2092cfe95169e8c992ec40295
   ├── 🍒 sha256:cbeec866936c4177184d1a17af697440ce3b67acb176d314876a3c8f0ca56f53
   ├── 🍒 sha256:575d374e029b5a8078878683894fa8bc32a88bb666c656d0bb9c30afccd2668c
   └── 🍒 sha256:c61a3bc4599bdb41b9734b039b68156a7304bd5de7b8df08679a203171b5d784
└── 🔐 Signatures for an image tag: cgr.dev/chainguard/nginx:sha256-475b56541eec5bf8ef725c8e8912dc1451e01d6065f0ceac7f6a39cb229fcfe2.sig
   └── 🍒 sha256:a921b47f93ddc97afd697d37b1f63527a32e1aa1a93e1a3068b6984e637adce9
└── 📦 SBOMs for an image tag: cgr.dev/chainguard/nginx:sha256-475b56541eec5bf8ef725c8e8912dc1451e01d6065f0ceac7f6a39cb229fcfe2.sbom
   └── 🍒 sha256:c67b16667b9e1e9dd520b654d93ace750a05169494636b2581079f827e4259c6
```

Not bad! In addition to a signature and SBOM, there are 4 other attestations available for this image that we could use to evaluate and make policy decisions
about whether or not we're comfortable using it in our environment.

## Conclusion

If you've made it this far, congratulations!

Have any ideas or feedback on this lab? Connect with me [on LinkedIn](https://linkedin.com/in/jonzeolla/) and send me a message.

Looking for more? Check out my [Container Security 201 lab](container-security-201).

## Cleanup

Don't forget to clean up your Cloud9 environment! Deleting the environment will terminate the EC2 instance as well.
