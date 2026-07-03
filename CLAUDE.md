# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CLI tool to control the **Anker Solix 3** solar battery system via its cloud API from the command line.

This is a greenfield project. The tech stack has not yet been decided. When it is chosen, update this file with build/test/lint commands and architecture notes.

## Stack Decisions (TBD)

Once a language/framework is chosen, document here:
- How to set up the dev environment
- How to build, run, and test
- How to run a single test

## What We Know

- Target: Anker Solix 3 API (cloud API, not local)
- Interface: CLI (command-line tool)
- Platform: OpenBSD (use `doas pkg_add -a` for missing packages)
- If Python is chosen: always use a virtualenv before `pip`
