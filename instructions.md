# Instructions for the RAG on IBM Power Systems Workshop

## Goal and purpose of this document

The document at hand consists of instructions to manually set up a _retrieval augmented generation_ (RAG) application on IBM Power systems (ppc64le). Therefore, three components are deployed: a large language model using the llama.cpp runtime, a vector database (ChromaDB), and a lightweight user interface to handle the interaction between the user and the forementioned components.

## Deployment of a large language model

Before starting with the setup of the large language model (LLM), the simultaneous multithreading (SMT) level is set to the value `2`. When working with large models, performance does not benefit from high SMT levels as the pipes are properly filled even on small levels. Feel free to experiment with different values for different models.

```shell
$ sudo ppc64_cpu --smt=2
```

During the setup phase, different (developer) tools are needed. Therefore, the Extra Package for Enterprise Linux (EPEL) is added and the CodeReady repository activated.

```shell
$ sudo subscription-manager repos --enable codeready-builder-for-rhel-$(rpm -E %rhel)-ppc64le-rpms
$ sudo rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-$(rpm -E %rhel)
$ sudo dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(rpm -E %rhel).noarch.rpm
```

Next, a working directory is created. In the example at hand, the working directory is called `llm` and located in the user's home directory.

```shell
$ pwd
/home/cecuser
$ mkdir llm && cd $_
```

> [!IMPORTANT]
> If you are running RHEL 10.0 (RHEL < 10 is probably also affected), you have to manually upgrade `rpm-sequoia` and `openssl-libs` before installing the `Development tools` package. At the time of this writing, `rpm-sequoia` contains a bug, which would lead to the inability to install any package after installing the wrong version of it. Upgrade via `sudo dnf upgrade rpm-sequoia openssl-libs`. >)

The `Development tools` package is installed ...

```shell
$ sudo dnf -y groupinstall 'Development tools'
```

... alongside other tools and libraries:

```shell
$ sudo dnf -y install \
    bzip2 \
    cmake \
    curl \
    gcc \
    git \
    openblas-devel \
    libcurl-devel \
    libxcrypt-compat \
    vim
```

> [!NOTE]
> If you are running on RHEL 9 or earlier, you may have to install `gcc-toolset-13` or newer to get a gcc version that is sufficient for subsequent tasks. As we are running on RHEL 10, the system version is fine.

_micromamba_ is used for dependency isolation and is subsequently installed.

```shell
$ curl -o /tmp/micromamba.tar.bz2 -L https://micro.mamba.pm/api/micromamba/linux-ppc64le/latest
$ tar -xf /tmp/micromamba.tar.bz2 --strip-components=1 bin/micromamba
$ sudo mv micromamba /usr/local/bin
$ rm /tmp/micromamba.tar.bz2
```

To initialise the current and all future shells, run the following three commands:

```shell
$ micromamba shell init --shell=bash
$ echo 'micromamba activate' >> ~/.bashrc
$ source ~/.bashrc
```

For all LLM-related dependencies, an environment with the name `llm` is created and Python 3.12 is installed:

```shell
$ micromamba create -y \
    -n llm \
	--channel=defaults \
	python=3.12
$ micromamba activate -n llm
```

The model runtime requires some Python packages. The crucial ones are optimised for ppc64le and available via IBM's _Devpi_.
To install packages from the Devpi, simply add the Devpi's index url as extra index url to all `pip install` commands and add the `--prefer-binary` flag to prefer binaries over source installations.
If Python's package manager pip can't find the corresponding package in the Devpi, it will fall back to the default PyPI.

Here's the command to install all dependencies:

```shell
$ python -m pip install \
    --prefer-binary \
    --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux \
    numpy \
    torch \
    sentencepiece \
    gguf
```

For simplicity, llama.cpp is used as a model runtime. While llama.cpp is suitable for production, too, vLLM is a scalable alternative that should be considered. To get all hardware optimisation, llama.cpp needs to be compiled from source. First, clone the llama.cpp repository:

```shell
$ pwd
/home/cecuser/llm
$ git clone https://github.com/ggerganov/llama.cpp.git
```

Create a `build` directory, configure cmake to use OpenBLAS, and compile llama.cpp:

```shell
$ mkdir llama.cpp/build && cd $_
$ cmake -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS ..
$ cmake --build . --config Release -j 8
$ chmod +x bin/llama-server
```

> [!NOTE]
> OpenBLAS provides llama.cpp with the capability to leverage the power of IBM Power‘s MMA units in the prompt intake phase. For simplicity, the `openblas-devel` package was installed.
> 
> For production scenarios (especially when using vLLM), consider compiling OpenBLAS from source with multi-threading support to boost the performance even further.

All models used in this workshop come from huggingface. To download models, install `huggingface_hub` including the `cli` and `hf_xet` (faster download) extras:

```shell
$ cd ../..
$ pwd
/home/cecuser/llm
$ mkdir models
$ python -m pip install -U "huggingface_hub[cli,hf_xet]"
```

llama.cpp only support models in GGUF format. Some projects publish models in GGUF format, others require converting them using different tools. The user _bartowski_ provides a big number of converted models in different data formats. In the example at hand, the **IBM Granite 4.0-H-Tiny** model is used:

```shell
$ hf download \
    bartowski/ibm-granite_granite-4.0-h-tiny-GGUF ibm-granite_granite-4.0-h-tiny-Q8_0.gguf \
    --local-dir models/bartowski/ibm-granite_granite-4.0-h-tiny-GGUF
```

Managing AI applications becomes easier, when knowing exactly how to manage them. Therefore, a new systems service responsible for llama.cpp is set up. Create a service-file `/etc/systemd/system/llama.cpp.service` with the following content:

```ini
[Unit]
Description=Llama.cpp Service

[Service]
Type=simple
ExecStart=/home/cecuser/llm/llama.cpp/build/bin/llama-server -m /home/cecuser/llm/models/bartowski/ibm-granite_granite-4.0-h-tiny-GGUF/ibm-granite_granite-4.0-h-tiny-Q8_0.gguf -v -c 12288 -t 32 -tb 32 --api-key examplekey001 --host 0.0.0.0 --port 8080
User=cecuser

[Install]
WantedBy=multi-user.target
```

A couple of parameters are passed on the `llama-server` executable. It includes the maximum context size (`-c`), host and port, as well as the number of used threats. The number of threats should be set to `<= cores * SMT level` (here `16 * 2 = 32`).

Reload the daemon and start the llama.cpp service:

```shell
$ sudo systemctl daemon-reload
$ sudo systemctl start llama.cpp
```

Check status and logs as follows:

```shell
$ systemctl status llama.cpp
$ sudo journalctl -u llama.cpp
```

llama.cpp provides a simple UI for interacting  available under `http://<LPAR IP>:8080`.
If asked for an API key, use the one we specified in the execution command of the service file (here `examplekey001`).

## Set up the vector database

_ChromaDB_ is a lightweight and easy-to-use vector database providing all the features we need in this workshop. For production scenarios, consider using a more scalable product like _Milvus_.

ChromaDB is (mostly) written in Rust. Hence, the Rust compiler is needed:

```shell
$ curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
$ . "$HOME/.cargo/env"
```

Next, protobuf is installed:

```shell
$ export PROTOBUF_VERSION=33.5
$ curl -LO https://github.com/protocolbuffers/protobuf/releases/download/v${PROTOBUF_VERSION}/protoc-${PROTOBUF_VERSION}-linux-ppcle_64.zip && unzip -o protoc-${PROTOBUF_VERSION}-linux-ppcle_64.zip -d $HOME/.local
```

We want to isolate chroma’s from llama.cpp’s dependencies. Hence, create a new micromamba environment called `chroma`:

```shell
$ micromamba create -y \
    -n chroma \
	--channel=defaults \
	python=3.12
$ micromamba activate -n chroma
```

Here again, a couple of IBM Power-optimised libraries are needed, as well as build tools. These dependencies are installed from the Devpi and PyPI:

```shell
$ python -m pip install \
    --prefer-binary \
    --extra-index-url=https://wheels.developerfirst.ibm.com/ppc64le/linux \
    build \
    maturin \
    numpy \
    onnxruntime \
    pillow \
    uvicorn
```

Next, clone the chroma repository …

```shell
$ cd ~/llm
$ git clone --depth 1 --branch 1.5.0 https://github.com/chroma-core/chroma.git
$ cd chroma
```

… and update the lock file to include the latest `generator-rs` version.

```shell
$ cargo update generator@0.8.1
```

> [!NOTE]
> The chromadb maintainer use unstable Rust versions in their development / latest branch, hence, we download the most recent release branch.

Execute the build command …

```shell
$ python -m build .
```

… and install the build result (Python wheel) in the activated micromamba environment:

```shell
$ cd dist
$ CC=/usr/bin/gcc python -m pip install --prefer-binary --extra-index-url https://wheels.developerfirst.ibm.com/ppc64le/linux *.whl
```

> [!IMPORTANT]
> Chroma has some more dependencies (like grpcio) that take long to compile. The added index url includes these packages as binaries.

> [!NOTE]
> If you are using `gcc-toolset-<VERSION>`, make sure to adjust the compiler path accordingly.

Tidy up some thing and remove the chroma directory entirely, as the installed wheel resides in a different location:

```shell
$ cd ../..
$ pwd
/home/cecuser/llm
$ rm -rf chroma
```

We will execute chroma in client-server mode. Therefore, a directory for storing database-related files is needed, which we create in our working directory:

```shell
$ mkdir db
```

Again, create a service-file `/etc/systemd/system/chromadb.service` with the following content for easier management of the chroma-process:

```ini
[Unit]
Description=ChromaDB Service

[Service]
Type=simple
ExecStart=/home/cecuser/.local/share/mamba/envs/chroma/bin/chroma run --path /home/cecuser/llm/db
User=cecuser

[Install]
WantedBy=multi-user.target
```

Reload the daemon and start the service:

```shell
$ sudo systemctl daemon-reload
$ sudo systemctl start chromadb
```

Check status and logs:

```shell
$ systemctl status chromadb
$ sudo journalctl -u chromadb
```

Now, an empty vector database is running on the LPAR. To insert documents, clone the git repository containing this instructions file on the target machine, as it also includes the documents we want to insert, the script for inserting the documents, and the application for this RAG use case.

```shell
$ pwd
/home/cecuser/llm
$ git clone https://github.com/AI-on-Power-DACH/rag-on-ppc64le-workshop.git
$ cd rag-on-ppc64le-workshop
```

Execute the `insert_documents.py` script, which creates a new collection per document, splits the documents into smaller chunks based on the chapters (one chapter = one chunk), and inserts them into the collection.

```shell
$ python src/insert_documents.py
```

## Deployment of the user interface

Lastly, we deploy a lightweight frontend responsible for the workflow. Therefore, we create a new service file called `/etc/systemd/system/frontend.service` with the following content:

```ini
[Unit]
Description=RAG Frontend Service

[Service]
Type=simple
ExecStart=/home/cecuser/.local/share/mamba/envs/chroma/bin/python /home/cecuser/llm/rag-on-ppc64le-workshop/src/app.py
User=cecuser

[Install]
WantedBy=multi-user.target
```

Before we can start the service, two more dependencies need to be installed (the `chroma` environment should still be activated):

```shell
$ python -m pip install gradio openai
```

Gradio is a library that let‘s you quickly build a frontend to for various AI use cases. As llama.cpp provides an openai-compatible API, the openai Python package can be used to send requests to the endpoint.

Reload the daemon and start the service:

```shell
$ sudo systemctl daemon-reload
$ sudo systemctl start frontend
```

Check status and logs:

```shell
$ systemctl status frontend
$ sudo journalctl -u frontend
```

The frontend is now available under `http://<LPAR IP ADDRESS>:7860`.

Congratulations for deploying your first RAG use case on ppc64le! 🎉
