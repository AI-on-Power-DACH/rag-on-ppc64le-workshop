# 🚀 RAG on IBM POWER Systems Workshop

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-ppc64le-red.svg)](https://www.ibm.com/power)

A comprehensive hands-on workshop for building and deploying **Retrieval Augmented Generation (RAG)** applications on IBM POWER Systems (ppc64le architecture).

## 📋 Overview

This repository provides everything you need to deploy a RAG application on IBM POWER Systems, featuring:

- 🤖 **LLM Runtime**: llama.cpp with IBM Granite 4.0-H-Tiny model
- 🗄️ **Vector Database**: ChromaDB for efficient document retrieval
- 🎨 **User Interface**: Gradio-based chat interface with IBM theming
- 📚 **Knowledge Base**: IBM RedBooks content on POWER systems, OpenShift, and Ansible

## 🏗️ Architecture

```
┌─────────────────┐
│  Gradio UI      │ ← User queries IBM RedBooks content
│  (Port 7860)    │
└────────┬────────┘
         │
         ├──────────────────┐
         │                  │
┌────────▼────────┐  ┌──────▼──────────┐
│  ChromaDB       │  │  llama.cpp      │
│  Vector Store   │  │  LLM Server     │
│  (Port 8000)    │  │  (Port 8080)    │
└─────────────────┘  └─────────────────┘
```

## 📂 Repository Structure

```
.
├── src/
│   ├── app.py                # Gradio frontend application
│   ├── ibm_theme.py          # IBM Design theme for Gradio
│   ├── insert_documents.py   # Document ingestion script
│   └── db_files/             # Knowledge base documents
│       ├── Ansible.md        # Ansible automation on POWER
│       ├── E1050.md          # IBM Power E1050 server
│       ├── E1080.md          # IBM Power E1080 server
│       ├── Openshift.md      # Red Hat OpenShift on POWER
│       └── Scale_OUT.md      # POWER Scale-Out servers
├── instructions.md           # Detailed deployment guide
├── LICENSE                   # Apache 2.0 License
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites

- IBM POWER system running RHEL 9/10 (ppc64le)
- Root or sudo access
- Internet connectivity for package downloads

### Deployment

Follow the comprehensive step-by-step instructions in [instructions.md](instructions.md) to:

1. **Deploy the LLM**: Set up llama.cpp with IBM Granite model
2. **Configure Vector DB**: Build and deploy ChromaDB from source
3. **Launch the UI**: Start the Gradio-based chat interface

The complete deployment takes approximately 30-45 minutes.

## 💡 Use Cases

This workshop demonstrates practical RAG applications for:

- 📖 **Technical Documentation Search**: Query IBM RedBooks and technical manuals
- 🔍 **Knowledge Management**: Build searchable knowledge bases from markdown documents
- 🤝 **IT Support**: Provide AI-assisted answers from internal documentation
- 🎓 **Training & Education**: Interactive learning from technical content
